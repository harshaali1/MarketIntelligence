<script setup>
import { ref, computed } from "vue";
import { useAuthStore } from "@/stores/auth_store";
import { useMessageStore } from "@/stores/message_store";
import { useRouter } from "vue-router";


// --- 1. CHART.JS IMPORTS ---
import { Line, Bar } from 'vue-chartjs'; 
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Filler
} from 'chart.js';

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  LineElement,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Filler
);

const authStore = useAuthStore();
const messageStore = useMessageStore();
const router = useRouter();

const backendURL = computed(() => authStore.getBackendServerURL());
const userId = computed(() => authStore.getUserId());

function getAuthHeaders() {
  const headers = { "Content-Type": "application/json" };
  const authToken = sessionStorage.getItem('auth_token');
  if (authToken) {
    headers["Authorization"] = authToken; // Try without "Bearer"
    headers["X-Auth-Token"] = authToken; // Also try custom header
  }
  console.log('DEBUG getAuthHeaders:', headers);
  return headers;
}

// --- State ---
const searchQuery = ref("");
const analysisResults = ref(null);
const analysisNews = ref([]);
const loading = ref(false);
const error = ref(null);
const watchlist = ref([]);

//CHART DATA REFERENCES
const priceChartData = ref(null);
const volumeChartData = ref(null);
const dmaChartData = ref(null); 

// --- Chart Options (ADJUSTED DENSITY FIX FOR FULL DATE) ---
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
    }
  },
  scales: {
    x: {
      type: 'category', 
      ticks: {
        // CRITICAL FIX: Adjusted density from 5 to 3 to make dates visible
        callback: function(val, index) {
          // Display the label for every 3rd index.
          if (index % 3 === 0) { 
            const dateStr = this.getLabelForValue(val);
            if (dateStr) {
                // NEW: Parse and format the date to ensure full date (YYYY-MM-DD) is displayed
                try {
                    const date = new Date(dateStr);
                    const year = date.getFullYear();
                    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
                    const day = String(date.getDate()).padStart(2, '0');
                    return `${year}-${month}-${day}`;
                } catch (e) {
                    // Fallback to original string if date parsing fails
                    return dateStr; 
                }
            }
            return '';
          }
          return null; // Hide the label for all other points
        },
        
        // NEW: Reinstated rotation to accommodate the longer date string
        maxRotation: 45, 
        minRotation: 45,
        autoSkip: true,
        autoSkipPadding: 5, // Adjusted padding
      },
      grid: {
        display: false 
      }
    },
    y: {
      grid: {
        color: 'rgba(200, 200, 200, 0.4)',
      }
    }
  }
};


// --- Modal State (Unchanged) ---
const showPredictModal = ref(false);
const predictedData = ref(null);
const predictLoading = ref(false);
const predictError = ref(null);

// --- NEW PORTFOLIO STATE ---
const showPortfolioModal = ref(false);
const portfolioTransaction = ref({
  ticker: '',
  company_name: '',
  price: 0,
  quantity: 1,
  purchase_date: new Date().toISOString().substring(0, 10) // YYYY-MM-DD
});


// --- Fetch Watchlist (Unchanged) ---
async function fetchWatchlist() {
  if (!userId.value) return;
  try {
    const res = await fetch(`${backendURL.value}/api/v1/watchlist/${userId.value}`, {
      headers: getAuthHeaders(),
    });
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (err) {
      console.warn("Watchlist JSON parse failed:", text, err);
    }
    watchlist.value = data?.watchlist || [];
  } catch (err) {
    console.error("Fetch watchlist failed:", err);
  }
}

const isTickerInWatchlist = computed(
  () => (ticker) => watchlist.value.some((i) => i.ticker === ticker.toUpperCase())
);

//Fetch Price Chart JSON Data (Unchanged)
async function fetchPriceChartData(ticker) {
  try {
    const url = `http://127.0.0.1:5001/api/v1/chart/price?stock=${ticker}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.error || `HTTP ${res.status}`);
    }
    priceChartData.value = data;
  } catch (err) {
    console.error("Price chart data load failed:", err);
    priceChartData.value = null; 
  }
}

//Fetch Volume Chart JSON Data (Unchanged)
async function fetchVolumeChartData(ticker) {
  try {
    const url = `http://127.0.0.1:5001/api/v1/chart/volume?stock=${ticker}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.error || `HTTP ${res.status}`);
    }
    volumeChartData.value = data;
  } catch (err) {
    console.error("Volume chart data load failed:", err);
    volumeChartData.value = null;
  }
}

//Fetch DMA Chart JSON Data (Unchanged)
async function fetchDMAChartData(ticker) {
  try {
    const url = `http://127.0.0.1:5001/api/v1/chart/dma?stock=${ticker}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.error || `HTTP ${res.status}`);
    }
    dmaChartData.value = data;
  } catch (err) {
    console.error("DMA chart data load failed:", err);
    dmaChartData.value = null;
  }
}


// --- Search & Analyze Ticker (Unchanged) ---
async function analyzeTicker() {
  const query = searchQuery.value.trim().toUpperCase();
  if (!query) return;

  loading.value = true;
  error.value = null;
  analysisResults.value = null;
  analysisNews.value = [];
  // Clear chart data
  priceChartData.value = null;
  volumeChartData.value = null;
  dmaChartData.value = null; 

  try {
    const url = `${backendURL.value}/api/v1/analyze?ticker=${query}&exchange=NS`;
    const res = await fetch(url, { headers: getAuthHeaders() });
    const text = await res.text();
    let data = null;

    try {
      data = text ? JSON.parse(text) : null;
    } catch (err) {
      console.warn("Analyze JSON parse failed:", text, err);
    }

    if (!res.ok || !data) throw new Error(data?.message || `HTTP ${res.status}`);

    const analysis = data.analysis;
    const news = data.news_headlines || [];

    analysisResults.value = {
      ticker: analysis.ticker,
      company_name: analysis.company_name,
      exchange: analysis.exchange,
      last_price: analysis.last_price || "N/A",
      previous_close: analysis.previous_close || "N/A",
      day_high: analysis.day_high || "N/A",
      day_low: analysis.day_low || "N/A",
      change_percent: analysis.change_percent || "N/A",
      volume: analysis.volume || "N/A",
      market_cap: analysis.market_cap || "N/A",
      sector: analysis.sector || "N/A",
      industry: analysis.industry || "N/A",
      summary: analysis.summary || "No summary available.",
      pe_ratio: analysis.pe_ratio || "N/A",
      pb_ratio: analysis.pb_ratio || "N/A",
    };

    analysisNews.value = news;

    // Fetch all chart JSON data simultaneously
    fetchPriceChartData(query);
    fetchVolumeChartData(query);
    fetchDMAChartData(query);
  } catch (err) {
    error.value = err.message || "Failed to fetch analysis data.";
  } finally {
    loading.value = false;
  }
}

// --- ADD TO WATCHLIST (Unchanged) ---
// --- ADD TO WATCHLIST (Unchanged) ---
async function addToWatchlist(ticker) {
  if (!userId.value) {
    messageStore.setFlashMessage("Please log in to save watchlist.");
    router.push("/login");
    return;
  }

  if (isTickerInWatchlist.value(ticker)) {
    messageStore.setFlashMessage(`${ticker} already in watchlist.`);
    return;
  }

  try {
    const res = await fetch(`${backendURL.value}/api/v1/watchlist/add`, {
      method: "POST",
      headers: { ...getAuthHeaders(), "user-id": userId.value.toString() },
      body: JSON.stringify({ ticker: ticker.toUpperCase(), notes: "" }),
    });

    const text = await res.text();
    let data = null;

    try {
      data = text ? JSON.parse(text) : null;
    } catch (err) {
      console.warn("Add watchlist JSON parse failed:", text, err);
    }

    if (!res.ok || !data) throw new Error(data?.message || "Failed to add.");

    messageStore.setFlashMessage(`${ticker} added to watchlist.`);
    await fetchWatchlist();
  } catch (err) {
    messageStore.setFlashMessage(err.message || "Failed to add to watchlist.");
  }
}


// --- Prediction Modal (Unchanged) ---
async function predictFuturePrice(ticker) {
  predictLoading.value = true;
  predictError.value = null;
  predictedData.value = null;
  showPredictModal.value = true;

  try {
    const url = `${backendURL.value}/api/v1/predict?stock=${ticker.toUpperCase()}`;
    const res = await fetch(url, { headers: getAuthHeaders() });
    const text = await res.text();
    let data = null;

    try {
      data = text ? JSON.parse(text) : null;
    } catch (err) {
      console.warn("Predict JSON parse failed:", text, err);
    }

    if (!res.ok || !data) throw new Error(data?.message || "Prediction failed");

    predictedData.value = data;
  } catch (err) {
    predictError.value = err.message || "Prediction failed.";
  } finally {
    predictLoading.value = false;
  }
}

// --- NEW PORTFOLIO FUNCTIONS ---
function openPortfolioModal() {
  if (!userId.value) {
    messageStore.setFlashMessage("Please log in to track your portfolio.");
    router.push("/login");
    return;
  }

  if (!analysisResults.value) return;

  // Initialize transaction data with current stock info
  portfolioTransaction.value = {
    ticker: analysisResults.value.ticker,
    company_name: analysisResults.value.company_name,
    // Use the current price, converting to a number for the input
    price: Number(analysisResults.value.last_price || 0).toFixed(2), 
    quantity: 1,
    // Current date in YYYY-MM-DD format
    purchase_date: new Date().toISOString().substring(0, 10) 
  };
  
  showPortfolioModal.value = true;
}

function saveToPortfolio() {
  if (!userId.value) return;

  const url = `${backendURL.value}/api/v1/portfolio/add`;
  
  fetch(url, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      user_id: userId.value,
      symbol: portfolioTransaction.value.ticker,
      quantity: portfolioTransaction.value.quantity,
      purchase_price: parseFloat(portfolioTransaction.value.price),
      purchase_date: portfolioTransaction.value.purchase_date,
      notes: portfolioTransaction.value.company_name
    })
  })
  .then(res => res.json())
  .then(() => {
    messageStore.setFlashMessage(`${portfolioTransaction.value.ticker} added to portfolio successfully!`);
    showPortfolioModal.value = false;
    portfolioTransaction.value = { ticker: '', company_name: '', price: 0, quantity: 1, purchase_date: new Date().toISOString().substring(0, 10) };
  })
  .catch(err => {
    messageStore.setFlashMessage(`Failed to add to portfolio: ${err.message}`);
  });

}


// --- Formatting (Updated/New Functions) ---
function formatPrice(price) {
  if (!price || price === "N/A") return "N/A";
  const num = Number(price);
  return isNaN(num) ? "N/A" : `₹${num.toFixed(2)}`;
}
function formatMarketCap(cap) {
  if (!cap || cap === "N/A") return "N/A";
  const num = Number(cap);
  return isNaN(num) ? "N/A" : `₹${num.toLocaleString("en-IN")}`;
}
function formatVolume(vol) {
  if (!vol || vol === "N/A") return "N/A";
  const num = Number(vol);
  return isNaN(num) ? "N/A" : num.toLocaleString("en-IN");
}
function formatDate(dateString) {
  if (!dateString || dateString === "N/A") return "N/A";
  try {
    const date = new Date(dateString);
    // Include year for news date
    return date.toLocaleDateString("en-IN", {
      year: "numeric", 
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return dateString.split(" ")[0];
  }
}

// NEW: Ratio Formatting (for P/E, P/B)
function formatRatio(ratio) {
  if (ratio === null || ratio === undefined || ratio === 'N/A') return "N/A";
  const num = Number(ratio);
  return isNaN(num) ? "N/A" : num.toFixed(2);
}


//Computed property to truncate the summary (UPDATED: Shorter limit)
const shortSummary = computed(() => {
  if (!analysisResults.value || !analysisResults.value.summary || analysisResults.value.summary === "No summary available.") {
    return "No summary available.";
  }
  const summary = analysisResults.value.summary;
  //CRITICAL CHANGE: Set a new, smaller character limit (e.g., 80 characters)
  const maxLength = 80; 

  if (summary.length <= maxLength) {
    return summary;
  }

  let truncated = summary.substring(0, maxLength);
  const lastSpace = truncated.lastIndexOf(' ');

  if (lastSpace !== -1) {
    truncated = truncated.substring(0, lastSpace);
  }

  return truncated.trim() + '...';
});


if (userId.value) fetchWatchlist();
</script>

<template>
  <div class="search-section">
    <h2 class="title">Stock Search & Analysis</h2>

    <form @submit.prevent="analyzeTicker" class="search-form">
      <input
        v-model.trim="searchQuery"
        type="text"
        placeholder="Enter stock ticker (e.g., TCS)"
        required
        class="search-input"
      />
      <button type="submit" class="btn-search" :disabled="loading">
        <span v-if="loading">Analyzing...</span>
        <span v-else>Analyze</span>
      </button>
    </form>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else-if="analysisResults" class="analysis-card">
      
      <div class="analysis-content-grid">
        
        <div class="details-column">
          <h3>{{ analysisResults.company_name }} ({{ analysisResults.ticker }})</h3>
          <p><strong>Exchange:</strong> {{ analysisResults.exchange }}</p>
          <p><strong>Current Price:</strong> {{ formatPrice(analysisResults.last_price) }}</p>
          <p><strong>Change:</strong> {{ analysisResults.change_percent }}%</p>
          <p><strong>Volume:</strong> {{ formatVolume(analysisResults.volume) }}</p>

          <hr /> 
          
          <h4>Price Points</h4>
          <p><strong>Day High:</strong> {{ formatPrice(analysisResults.day_high) }}</p>
          <p><strong>Day Low:</strong> {{ formatPrice(analysisResults.day_low) }}</p>
          <p><strong>Prev. Close:</strong> {{ formatPrice(analysisResults.previous_close) }}</p>
          
          <hr class="desktop-only" /> 
          
          <h4>Valuation & Metrics</h4>
          <p><strong>Market Cap:</strong> {{ formatMarketCap(analysisResults.market_cap) }}</p>
          
          <p><strong>P/E Ratio:</strong> {{ formatRatio(analysisResults.pe_ratio) }}</p>
          <p><strong>P/B Ratio:</strong> {{ formatRatio(analysisResults.pb_ratio) }}</p>
          
          <p><strong>Sector:</strong> {{ analysisResults.sector }}</p>
          <p><strong>Industry:</strong> {{ analysisResults.industry }}</p>

          <h4 class="summary-heading">Summary</h4>
          <p class="summary">{{ shortSummary }}</p>

          <div class="button-group">
            <button
              @click="addToWatchlist(analysisResults.ticker)"
              :disabled="isTickerInWatchlist(analysisResults.ticker)"
              class="btn-add"
            >
              {{ isTickerInWatchlist(analysisResults.ticker)
                ? "Already in Watchlist"
                : "Add to Watchlist" }}
            </button>

            <button @click="openPortfolioModal" class="btn-portfolio">
              Add to Portfolio
            </button>
            
            <button @click="predictFuturePrice(analysisResults.ticker)" class="btn-predict">
              Predict Future Price
            </button>
          </div>
          
        </div> 
        
        <div class="charts-column">
          <div v-if="dmaChartData" class="chart-box">
            <h4>Moving Averages (Price, 50 DMA, 200 DMA)</h4>
            <div class="chart-container">
                <Line :data="dmaChartData" :options="chartOptions" />
            </div>
          </div>
          
          <div v-if="priceChartData" class="chart-box">
            <h4>Price Chart (6 Months)</h4>
            <div class="chart-container">
                <Line :data="priceChartData" :options="chartOptions" />
            </div>
          </div>

          <div v-if="volumeChartData" class="chart-box">
            <h4>Volume Chart</h4>
            <div class="chart-container">
                <Bar :data="volumeChartData" :options="chartOptions" />
            </div>
          </div>
        </div> 

      </div> 
      
      <div class="news-section full-width-news" v-if="analysisNews.length > 0">
        <h4>Related News</h4>
        <ul class="news-list">
          <li v-for="(news, i) in analysisNews" :key="i">
            <a :href="news.link" target="_blank">{{ news.title }}</a>
            <p class="news-meta">
              {{ news.source }} | {{ formatDate(news.published_at) }}
            </p>
          </li>
        </ul>
      </div>

    </div>

    <div v-if="showPredictModal" class="modal-backdrop" @click.self="showPredictModal = false">
      <div class="modal-content">
        <h3>Predicted Future Price: {{ analysisResults?.ticker }}</h3>

        <div v-if="predictLoading">Predicting...</div>
        <div v-else-if="predictError" class="error">{{ predictError }}</div>

        <div v-else-if="predictedData">
          <p>
            <strong>Last Price ({{ predictedData.last_date }}):</strong>
            {{ formatPrice(predictedData.last_price) }}
          </p>
          <p>
            <strong>Day 7 ({{ predictedData.day_7.date }}):</strong>
            {{ formatPrice(predictedData.day_7.price) }}
          </p>
          <p>
            <strong>Day 14 ({{ predictedData.day_14.date }}):</strong>
            {{ formatPrice(predictedData.day_14.price) }}
          </p>
        </div>

        <button @click="showPredictModal = false" class="btn-close">Close</button>
      </div>
    </div>
    
    <div v-if="showPortfolioModal" class="modal-backdrop" @click.self="showPortfolioModal = false">
      <div class="modal-content portfolio-modal">
        <h3>Add Transaction for: {{ portfolioTransaction.ticker }}</h3>
        <p>
          **{{ portfolioTransaction.company_name }}**
        </p>

        <form @submit.prevent="saveToPortfolio" class="portfolio-form">
          <div class="form-group">
            <label for="price">Purchase Price (₹):</label>
            <input
              id="price"
              type="number"
              step="0.01"
              v-model.number="portfolioTransaction.price"
              required
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label for="quantity">Quantity:</label>
            <input
              id="quantity"
              type="number"
              v-model.number="portfolioTransaction.quantity"
              min="1"
              required
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="date">Purchase Date:</label>
            <input
              id="date"
              type="date"
              v-model="portfolioTransaction.purchase_date"
              required
              class="form-input"
            />
          </div>

          <div class="modal-button-group">
              <button type="submit" class="btn-save">Save Transaction</button>
              <button type="button" @click="showPortfolioModal = false" class="btn-close">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.charts-column {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.chart-box {
  background: #f1f5f9;
  padding: 1rem;
  border-radius: 0.75rem;

  /* Ensure each chart gets its own fixed height */
  height: 350px;

  /* Prevent content from collapsing */
  display: flex;
  flex-direction: column;
}

.chart-container {
  flex: 1; /* Chart must expand inside parent, not overflow */
  min-height: 0; /* Prevent Chart.js from overflowing */
}


.search-section {
  padding: 1.5rem;
  margin-top: 1.5rem;
  background: #f9fafb;
  border-radius: 1rem;
  
  max-width: 1800px; 
  width: 95%; /* Use 95% of the viewport width */
  margin-left: auto;
  margin-right: auto;
}

/* ======================================= */
/* --- TWO-COLUMN FLEXBOX LAYOUT (Charts and Details) --- */
/* ======================================= */
.analysis-card {
  background: white;
  padding: 1rem;
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
}

.analysis-content-grid {
    display: flex;
    flex-direction: column; /* Default to stack columns on small screens */
    gap: 1.5rem; /* Space between columns */
    padding-bottom: 1rem; /* Space before the news section */
}

/* Apply side-by-side layout for tablets and larger screens (min-width 768px) */
@media (min-width: 768px) {
    .analysis-content-grid {
        flex-direction: row; /* Layout columns horizontally */
    }

    /* Left column (30%) */
    .details-column {
        flex: 1 1 30%; 
        min-width: 300px;
        padding-right: 1.5rem; 
        border-right: 1px solid #e2e8f0; 
        display: flex;
        flex-direction: column; 
    }

    /* Right column (70%) */
    .charts-column {
        flex: 1 1 70%; 
        display: flex;
        flex-direction: column;
        gap: 0; 
    }
    
    .desktop-only {
        display: none;
    }
}

/* ======================================= */
/* --- SEPARATE NEWS SECTION STYLING --- */
/* ======================================= */
.news-section {
    padding-top: 1rem;
    margin-top: 1rem;
    border-top: 1px solid #e2e8f0;
}

/* Multi-column layout for the news list on all screens larger than mobile */
@media (min-width: 600px) {
    .news-list {
        /* Use column layout to split the list items into two columns */
        column-count: 2;
        column-gap: 2rem; /* Increased gap for better reading */
        list-style: disc; 
        list-style-position: inside; 
    }

    /* Prevent list items from breaking across columns (if possible) */
    .news-list li {
        break-inside: avoid-column;
    }
}


.title {
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 1rem;
}
.search-form {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.search-input {
  flex: 1;
  padding: 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.5rem;
}
.btn-search {
  background-color: #0f0a0a;
  color: #edf5f2; /* Green */
    border-radius: 0.3rem;
    padding: 0.5rem 0.8rem;
    font-size: 0.85rem;
    cursor: pointer;
    transition: background-color 0.2s ease;
    white-space: nowrap;
}

/* Button Group Styling */
.button-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-top: 1rem;
}

.btn-add {
    color: #1c4587;
  background-color: #e6f0ff;
  border: none;
  border-radius: 0.3rem;
  padding: 0.5rem 0.8rem;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
  white-space: nowrap;
}
.btn-predict {
    color: #103571;
  background-color: #e6f0ff;
  border: none;
  border-radius: 0.3rem;
  padding: 0.5rem 0.8rem;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
  white-space: nowrap;
}
.btn-portfolio {
    color: #1a458a;
  background-color: #e6f0ff;
  border: none;
  border-radius: 0.3rem;
  padding: 0.5rem 0.8rem;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
  white-space: nowrap;
}

/* Modal Styling */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-content {
  background: white;
  padding: 1.5rem;
  border-radius: 0.75rem;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.btn-close {
  color: #3b82f6;
  background-color: #e04815;
  border: none;
  border-radius: 0.3rem;
  padding: 0.5rem 0.8rem;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
  white-space: nowrap;
}
.btn-save {
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
/* Portfolio Form Specific Styling */
.portfolio-form {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    margin-top: 1rem;
}
.form-group {
    display: flex;
    flex-direction: column;
}
.form-group label {
    font-weight: 500;
    margin-bottom: 0.2rem;
    font-size: 0.9rem;
}
.form-input {
    padding: 0.6rem;
    border: 1px solid #cbd5e1;
    border-radius: 0.5rem;
}
.modal-button-group {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 1rem;
    transition: background-color 0.2s ease;
}
</style>