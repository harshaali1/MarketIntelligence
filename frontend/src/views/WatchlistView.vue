<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth_store'
import { useMessageStore } from '@/stores/message_store'
import axios from 'axios'

// --- Chart.js imports ---
import { Chart, registerables } from 'chart.js'
import 'chartjs-adapter-date-fns' // CRITICAL: For time scale support
import { CandlestickController, CandlestickElement } from 'chartjs-chart-financial'

// Register all necessary components
Chart.register(...registerables, CandlestickController, CandlestickElement)

// --- Initialize Stores ---
const authStore = useAuthStore()
const messageStore = useMessageStore()

// --- Reactive State ---
const watchlist = ref([])
const watchlistLoading = ref(false)
const watchlistError = ref(null)

// Monte Carlo modal state
const showMonteCarloModal = ref(false)
const monteCarloData = ref(null)
const monteLoading = ref(false)
const monteError = ref(null)

// Technical Signal modal state
const showSignalModal = ref(false)
const signalData = ref(null)
const signalLoading = ref(false)
const signalError = ref(null)

// Chart Modal state
const showChartModal = ref(false)
// Initialized as an array for safe use with .length in template
const chartData = ref([]) 
const chartLoading = ref(false)
const chartError = ref(null)
const chartSymbol = ref('')
const candleChart = ref(null) // Template ref for the canvas
let chartInstance = null // To hold the chart instance for destruction

// --- Computed Properties ---
const backendURL = computed(() => authStore.getBackendServerURL())
const token = computed(() => authStore.getToken())
const userId = computed(() => authStore.getUserId())

const signalClass = computed(() => {
  if (!signalData.value || !signalData.value.signal) return ''
  return signalData.value.signal.toLowerCase().replace(/\s/g, '-').replace(/\(|\)/g, '')
})

// --- Helper Functions ---
function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' }
  if (token.value) headers['Authorization'] = `Bearer ${token.value}`
  return headers
}

// --- Fetch Watchlist ---
async function fetchWatchlist() {
  if (!userId.value) return
  watchlistLoading.value = true
  watchlistError.value = null

  try {
    const url = `${backendURL.value}/api/v1/watchlist/${userId.value}`
    const res = await fetch(url, { headers: getAuthHeaders() })

    if (!res.ok) throw new Error('Failed to fetch watchlist')

    const data = await res.json()
    watchlist.value = (data.watchlist || []).map(item => ({
        ...item,
        price: Number(item.price)
    }))
  } catch (err) {
    watchlistError.value = err.message
    messageStore.setFlashMessage(`Error: ${err.message}`)
  } finally {
    watchlistLoading.value = false
  }
}

// --- Delete from Watchlist ---
async function deleteFromWatchlist(id, ticker) {
  try {
    const url = `${backendURL.value}/api/v1/watchlist/${id}`
    const res = await fetch(url, { method: 'DELETE', headers: getAuthHeaders() })

    if (!res.ok) throw new Error(`Failed to delete ${ticker}`)

    watchlist.value = watchlist.value.filter(i => i.id !== id)
    messageStore.setFlashMessage(`Removed ${ticker} from watchlist`)
  } catch (err) {
    messageStore.setFlashMessage(`Error: ${err.message}`)
  }
}

// --- Monte Carlo Simulation ---
async function predictMonteCarlo() {
  if (!watchlist.value.length) return

  monteLoading.value = true
  monteError.value = null
  monteCarloData.value = null
  showMonteCarloModal.value = true

  try {
    const stocks = watchlist.value.map(s => s.ticker)

    const res = await fetch(`${backendURL.value}/api/v1/montecarlo`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ stocks })
    })

    const data = await res.json()
    if (!res.ok || data.error) throw new Error(data.error || 'Monte Carlo simulation failed')

    monteCarloData.value = {
      stocks: data.stocks || stocks,
      expected_return: Number(data.expected_return_percent ?? 0),
      volatility: Number(data.volatility_percent ?? 0),
      worst_5_percent: Number(data.worst_5_percent_percent ?? 0),
      conclusion: data.conclusion || 'No conclusion'
    }
  } catch (err) {
    monteError.value = err.message || 'Monte Carlo simulation failed'
  } finally {
    monteLoading.value = false
  }
}

// --- Technical Signal ---
async function getTechnicalSignal(ticker) {
  signalLoading.value = true
  signalError.value = null
  signalData.value = null
  showSignalModal.value = true

  try {
    const url = `${backendURL.value}/api/v1/technical_signal?stock=${ticker}`
    const res = await fetch(url, { headers: getAuthHeaders() })

    const data = await res.json()
    if (!res.ok || data.error) throw new Error(data.error || 'Failed to fetch signal')

    signalData.value = data
  } catch (err) {
    signalError.value = err.message || `Failed to get signal for ${ticker}`
  } finally {
    signalLoading.value = false
  }
}

// --- Fetch Candlestick Chart ---
async function fetchChartData(symbol) {
  chartSymbol.value = symbol
  chartLoading.value = true
  chartError.value = null
  chartData.value = [] // Reset data
  showChartModal.value = true // Open modal immediately

  try {
    const apiSymbol = symbol
    const url = `${backendURL.value}/api/v1/chart/candle/${apiSymbol}`
    
    const res = await axios.get(url, {
      headers: getAuthHeaders()
    })

    let responseData = res.data

    // Your API returns: { symbol, count, data: [...] }
    let rawData = responseData.data || responseData.chart_data || []

    // Sort by date
    rawData.sort((a, b) => new Date(a.Date) - new Date(b.Date))

    chartData.value = rawData
    
    // Give the DOM extra time to render
    await nextTick()
    await nextTick()
  
    
    // Force render after data is set
    if (showChartModal.value) {
      await renderChart()
    }
  
    
  } catch (err) {
    console.error('=== CHART FETCH ERROR ===')
    console.error('Error object:', err)
    console.error('Error name:', err.name)
    console.error('Error message:', err.message)
    console.error('Error stack:', err.stack)
    
    if (err.response) {
      console.error('Has response object')
      console.error('Response status:', err.response.status)
      console.error('Response statusText:', err.response.statusText)
      console.error('Response data:', err.response.data)
      console.error('Response headers:', err.response.headers)
      chartError.value = err.response.data?.error || `Server error: ${err.response.status}`
    } else if (err.request) {
      console.error('Has request but no response')
      console.error('Request:', err.request)
      chartError.value = 'No response from server. Check network/CORS.'
    } else {
      console.error('Error during request setup:', err.message)
      chartError.value = err.message || 'Failed to fetch chart data'
    }
    
    chartData.value = []
  } finally {
    chartLoading.value = false
    console.log('=== CHART FETCH COMPLETE ===')
  }
}

// --- Core function to render the chart ---
async function renderChart() {
  // Wait a bit to ensure DOM is ready
  await nextTick()
  
  if (!candleChart.value) {
    console.error('Canvas element not found')
    return
  }
  
  if (!chartData.value || chartData.value.length === 0) {
    console.error('No chart data available')
    return
  }
  
  const ctx = candleChart.value.getContext('2d')
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  // Map OHLC data, ensuring conversion to Number
  const ohlc = chartData.value.map(d => ({
    x: new Date(d.Date).getTime(),
    o: Number(d.Open), 
    h: Number(d.High),
    l: Number(d.Low),
    c: Number(d.Close)
  }))
  
  // Map SMA data - filter out null values
  const sma5 = chartData.value
    .filter(d => d.SMA5 !== null && d.SMA5 !== undefined)
    .map(d => ({ x: new Date(d.Date).getTime(), y: Number(d.SMA5) }))
  
  const sma20 = chartData.value
    .filter(d => d.SMA20 !== null && d.SMA20 !== undefined)
    .map(d => ({ x: new Date(d.Date).getTime(), y: Number(d.SMA20) }))

  chartInstance = new Chart(ctx, {
    type: 'candlestick',
    data: {
      datasets: [
        { 
          label: `${chartSymbol.value} OHLC`, 
          data: ohlc,
          borderWidth: 1,
          borderColor: function(context) {
            const item = context.raw
            return item.c >= item.o ? '#10b981' : '#ef4444'
          },
          backgroundColor: function(context) {
            const item = context.raw
            return item.c >= item.o ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)'
          }
        },
        // Line chart for SMA5
        {
          label: 'SMA5',
          data: sma5,
          type: 'line',
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.1,
          fill: false
        },
        // Line chart for SMA20
        {
          label: 'SMA20',
          data: sma20,
          type: 'line',
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.1,
          fill: false
        }
      ]
    },
    options: { 
        responsive: true, 
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: 'index'
        },
        plugins: { 
            legend: { 
                display: true, 
                position: 'top',
                labels: {
                    usePointStyle: true,
                    padding: 15,
                    font: {
                      size: 12
                    }
                }
            },
            tooltip: {
              enabled: true,
              callbacks: {
                label: function(context) {
                  const label = context.dataset.label || ''
                  if (context.parsed.y !== undefined) {
                    return `${label}: ₹${context.parsed.y.toFixed(2)}`
                  }
                  if (context.raw.o !== undefined) {
                    return [
                      `O: ₹${context.raw.o.toFixed(2)}`,
                      `H: ₹${context.raw.h.toFixed(2)}`,
                      `L: ₹${context.raw.l.toFixed(2)}`,
                      `C: ₹${context.raw.c.toFixed(2)}`
                    ]
                  }
                  return label
                }
              }
            }
        },
        scales: {
            y: {
                beginAtZero: false,
                title: {
                    display: true,
                    text: 'Price (₹)',
                    font: {
                      size: 12,
                      weight: 'bold'
                    }
                },
                ticks: {
                  callback: function(value) {
                    return '₹' + value.toFixed(0)
                  }
                },
                grid: {
                  color: 'rgba(0, 0, 0, 0.05)'
                }
            },
            x: {
                type: 'time',
                time: {
                    unit: 'day',
                    tooltipFormat: 'MMM dd, yyyy',
                    displayFormats: {
                        day: 'MMM dd',
                        week: 'MMM dd',
                        month: 'MMM yyyy'
                    }
                },
                title: {
                    display: true,
                    text: 'Date',
                    font: {
                      size: 12,
                      weight: 'bold'
                    }
                },
                grid: {
                  color: 'rgba(0, 0, 0, 0.05)'
                }
            }
        }
    }
  })
  
  console.log('Chart instance created:', chartInstance)
}

// --- Watchers for data loading and rendering ---

// 1. Watch chartData: When data is loaded/updated, try to render if the modal is already visible.
watch(chartData, async (newData) => {
  if (newData.length > 0 && showChartModal.value) {
    // Multiple nextTick calls to ensure DOM is fully ready
    await nextTick()
    await nextTick()
    renderChart()
  }
})

// 2. Watch showChartModal: When the modal opens, ensure data is ready and render.
watch(showChartModal, async (isVisible) => {
    if (isVisible && chartData.value.length > 0) {
        // Multiple nextTick calls to ensure v-if renders completely
        await nextTick()
        await nextTick()
        renderChart()
    } else if (!isVisible && chartInstance) {
        // Destroy the chart when modal closes to free memory
        chartInstance.destroy()
        chartInstance = null
    }
})

// --- Watch userId to fetch watchlist ---
watch(userId, (id) => {
  if (id) fetchWatchlist()
}, { immediate: true })
</script>

<template>
  <div class="watchlist-view">
    <div class="header-section">
      <h2 class="title">Your Watchlist ({{ watchlist.length }} stocks)</h2>
      <button v-if="watchlist.length" @click="predictMonteCarlo" class="run-monte-carlo-btn">
        Run Monte Carlo Simulation
      </button>
    </div>

    <div v-if="watchlistLoading">Fetching Data...</div>
    <div v-else-if="watchlistError" class="error">{{ watchlistError }}</div>
    <div v-else-if="!watchlist.length" class="empty">No items in watchlist.</div>

    <ul v-else class="list">
      <li v-for="item in watchlist" :key="item.id" class="stock-item-card">
        <div class="stock-info-main">
          <div class="ticker-and-change">
            <span class="ticker-name">{{ item.ticker }}</span>
            <span :class="['percentage-change', item.change_direction === 'up' ? 'positive' : 'negative']">
              <span v-if="item.change_direction === 'up'">▲</span>
              <span v-else-if="item.change_direction === 'down'">▼</span>
              {{ item.percentage_change }}%
            </span>
          </div>
          <span class="company-name">{{ item.company_name }}</span>
          <div class="price-info">
            <span class="label">Price</span>
            <span class="value">{{ item.price.toFixed(2) }}</span>
          </div>
        </div>

        <div class="stock-details">
          <div class="detail-group"><span class="label">Market Cap</span><span class="value">{{ item.market_cap }}</span></div>
          <div class="detail-group"><span class="label">Volume</span><span class="value">{{ item.volume }}</span></div>
          <div class="detail-group"><span class="label">P/E Ratio</span><span class="value">{{ item.pe_ratio }}</span></div>
        </div>

        <div class="actions">
          <button @click="getTechnicalSignal(item.ticker)" class="btn-action bullish-bearish">Bullish/Bearish</button>
          <button @click="fetchChartData(item.ticker)" class="btn-action chart-btn">View Chart</button>
          <button @click="deleteFromWatchlist(item.id, item.ticker)" class="btn-delete">🗑</button>
        </div>
      </li>
    </ul>

    <div v-if="showMonteCarloModal" class="modal-backdrop" @click.self="showMonteCarloModal = false">
      <div class="modal-content">
        <h3>Monte Carlo Portfolio Simulation</h3>
        <div v-if="monteLoading">Simulating...</div>
        <div v-else-if="monteError" class="error">{{ monteError }}</div>
        <div v-else-if="monteCarloData">
          <p><strong>Stocks:</strong> {{ monteCarloData.stocks.join(', ') }}</p>
          <p><strong>Expected Return:</strong> {{ monteCarloData.expected_return }}%</p>
          <p><strong>Volatility:</strong> {{ monteCarloData.volatility }}%</p>
          <p><strong>Worst 5%:</strong> {{ monteCarloData.worst_5_percent }}%</p>
          <p><strong>Conclusion:</strong> {{ monteCarloData.conclusion }}</p>
        </div>
        <button @click="showMonteCarloModal = false" class="btn-close">Close</button>
      </div>
    </div>

    <div v-if="showSignalModal" class="modal-backdrop" @click.self="showSignalModal = false">
      <div class="modal-content signal-modal">
        <h3>Technical Signal Analysis</h3>
        <div v-if="signalLoading">Analyzing Stock Data...</div>
        <div v-else-if="signalError" class="error">{{ signalError }}</div>
        <div v-else-if="signalData">
          <h4>{{ signalData.ticker }}</h4>
          <p><strong>Price:</strong> ₹{{ signalData.current_price.toFixed(2) }}</p>
          <div :class="['signal-box', signalClass]">
            <strong>Signal: {{ signalData.signal }}</strong>
            <p class="action-text">{{ signalData.suggested_action }}</p>
          </div>
          <p class="commentary">{{ signalData.commentary }}</p>
        </div>
        <button @click="showSignalModal = false" class="btn-close">Close</button>
      </div>
    </div>

    <div v-if="showChartModal" class="modal-backdrop" @click.self="showChartModal = false">
      <div class="modal-content chart-modal">
        <h3>{{ chartSymbol }} - Candlestick Chart</h3>
        
        <div v-if="chartLoading" class="chart-loading">Loading chart...</div>
        <div v-else-if="chartError" class="error">{{ chartError }}</div>
        <div v-else-if="chartData.length === 0" class="chart-empty">No chart data available.</div>
        
        <!-- Always render canvas when not loading/error, use v-show for visibility -->
        <div v-show="!chartLoading && !chartError && chartData.length > 0" class="chart-container">
          <canvas ref="candleChart"></canvas>
        </div>
        
        <button @click="showChartModal = false" class="btn-close">Close</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ================= GENERAL LAYOUT ================= */
.watchlist-view {
  font-family: 'Inter', sans-serif;
  background-color: #f7f8fc;
  padding: 1.5rem;
}

/* --- Header Section --- */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
  margin: 0;
}

/* Run Monte Carlo button */
.run-monte-carlo-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: #090410;
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.run-monte-carlo-btn:hover {
  background-color: #07040c;
}

.run-monte-carlo-btn svg {
  fill: currentColor;
}

/* --- Empty/Error/Loading States --- */
.empty {
  text-align: center;
  padding: 2rem;
  background-color: #fff;
  border-radius: 0.75rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  color: #555;
}

.error {
  color: #ef4444;
}

/* ================= STOCK LIST CARD ================= */
.list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.stock-item-card {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  padding: 1.2rem 1.5rem;
  display: grid;
  grid-template-columns: 1.2fr 2fr 1fr; /* Main | Details | Actions */
  align-items: center;
  gap: 1.5rem;
}

/* --- Left Section: Ticker, Company, Price --- */
.stock-info-main {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.ticker-and-change {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.ticker-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: #333;
}

.company-name {
  font-size: 0.85rem;
  color: #718096;
}

.price-info {
  margin-top: 0.5rem;
  display: flex;
  gap: 0.5rem;
}

.price-info .label {
  font-weight: 500;
  color: #a0aec0;
}

.price-info .value {
  font-weight: 600;
  color: #1a202c;
}

/* Price Change Chip */
.percentage-change {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.4rem;
  border-radius: 0.3rem;
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
}

.percentage-change.positive {
  background-color: #e6ffed; /* Light green */
  color: #276749; /* Dark green */
}

.percentage-change.negative {
  background-color: #fff0f0; /* Light red */
  color: #9b2c2c; /* Dark red */
}

/* ================= MIDDLE SECTION: DETAILS ================= */
.stock-details {
  display: flex;
  justify-content: space-around;
  text-align: left;
}

.detail-group {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.detail-group .label {
  font-size: 0.8rem;
  color: #a0aec0;
  margin-bottom: 0.1rem;
}

.detail-group .value {
  font-size: 0.95rem;
  font-weight: 500;
  color: #4a5568;
}

/* ================= RIGHT SECTION: ACTION BUTTONS ================= */
.actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
}

.btn-action {
  color: #3b82f6;
  background-color: #e6f0ff;
  border: none;
  border-radius: 0.3rem;
  padding: 0.5rem 0.8rem;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
  white-space: nowrap;
}

.btn-action:hover {
  background-color: #cce0ff;
}

.btn-action.chart-btn {
  background-color: #f0f7ff;
  color: #3b82f6;
}

.btn-delete {
  background: #fdf2f2;
  border: none;
  color: #ef4444;
  width: 35px;
  height: 35px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1rem;
}

.btn-delete:hover {
  background-color: #ffe0e0;
}

/* ================= MODAL STYLES ================= */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.modal-content {
  background: white;
  padding: 1.5rem;
  border-radius: 0.75rem;
  width: 350px;
  max-width: 90%;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* --- CHART MODAL --- */
.chart-modal {
  width: 90%;
  max-width: 800px;
  height: 85vh; 
  display: flex;
  flex-direction: column;
}

.chart-container {
  flex-grow: 1;
  position: relative;
  min-height: 400px;
}

.chart-modal canvas {
  width: 100% !important;
  height: 100% !important;
}

.chart-loading,
.chart-empty {
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: #718096;
}

.btn-close {
  margin-top: 1rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
  cursor: pointer;
}

/* ================= SIGNAL MODAL ================= */
.signal-box {
  margin: 1rem 0;
  padding: 1rem;
  border-radius: 0.5rem;
  text-align: center;
}

.strong-bullish, .bullish-weak, .neutral-to-bullish {
  background-color: #e6ffed;
  border: 1px solid #48bb78;
  color: #276749;
}

.strong-bearish, .bearish-weak, .neutral-to-bearish {
  background-color: #fff5f5;
  border: 1px solid #f56565;
  color: #9b2c2c;
}

.neutral {
  background-color: #f7fafc;
  border: 1px solid #a0aec0;
  color: #4a5568;
}

.strong-bullish {
  box-shadow: 0 0 5px rgba(72, 187, 120, 0.5);
}

.strong-bearish {
  box-shadow: 0 0 5px rgba(245, 101, 101, 0.5);
}

.action-text {
  font-size: 1.1rem;
  margin-top: 0.5rem;
}

.commentary {
  font-size: 0.9rem;
  color: #718096;
  margin-top: 1rem;
  border-top: 1px dashed #e2e8f0;
  padding-top: 0.5rem;
}
</style>