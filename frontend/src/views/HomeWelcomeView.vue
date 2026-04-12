<script setup>
import { RouterLink } from 'vue-router';
import { DotLottieVue } from '@lottiefiles/dotlottie-vue';

</script>

<template>
  <div class="marketiq-homepage">
    
    <section class="hero-section">
      <DotLottieVue 
        class="corner-lottie"
        autoplay 
        loop 
        src="https://lottie.host/cdf5dae0-fa94-4351-86bb-83e6f51896ff/hlHQ6zpVR9.lottie" 
      />
      
      <DotLottieVue 
        class="right-corner-lottie"
        autoplay 
        loop 
        src="https://lottie.host/a32942ae-20c3-4c38-87d5-9a0d5456b6fa/kRf35mAKv5.lottie" 
      />

      <div class="lottie-container">
        <DotLottieVue 
          class="hero-lottie"
          autoplay 
          loop 
          src="https://lottie.host/ab88ee0c-2806-476f-8738-c46a9dbc7325/qb6k3WxPjR.lottie" 
        />
      </div>

      <h1 class="hero-title">Stock Market Intelligence</h1>
      <p class="hero-subtitle">
        Access real-time market insights, advanced price predictions, and intelligent recommendations for informed investment decisions.
      </p>
      <div class="hero-actions">
        <RouterLink to="/signup" class="btn primary-cta">
          Begin Your Journey <span class="arrow">→</span>
        </RouterLink>
        <RouterLink to="/login" class="btn secondary-cta">
          Sign In
        </RouterLink>
      </div>
    </section>

    <section class="features-section">
      <div class="feature-card">
        <div class="icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
        </div>
        <h3 class="card-title">Market Analytics</h3>
        <p class="card-description">
          Access comprehensive charts and live market data with advanced technical indicators.
        </p>
      </div>

      <div class="feature-card">
        <div class="icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 15V20H22V15"></path>
            <path d="M17 10H14L10 14L7 11L2 16"></path>
          </svg>
        </div>
        <h3 class="card-title">Price Predictions</h3>
        <p class="card-description">
          Leverage advanced algorithms for accurate stock price forecasting and trend analysis.
        </p>
      </div>

      <div class="feature-card">
        <div class="icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
        </div>
        <h3 class="card-title">Smart Insights</h3>
        <p class="card-description">
          Receive data-driven recommendations based on comprehensive market analysis.
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* --- General Styles --- */
.marketiq-homepage {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #1a1a2e;
  background-color: #ffffff;
  min-height: 100vh;
  position: relative; 
}

/* --- Hero Section Styles (Centerpiece) --- */
.hero-section {
  text-align: center;
  padding: 4rem 2rem 3rem; 
  max-width: 900px;
  margin: 0 auto;
  position: relative; 
}

/* ✅ Left Corner Lottie: Syntax Verified */
.corner-lottie {
  position: absolute; 
  
  /* CRITICAL FIX: Ensure spaces around '-' signs in calc() */
  left: calc(50% - 450px - 160px - 20px); 
  
  top: 300px;       
  
  width: 160px;    
  height: 160px;   
  z-index: 10;     
}

/* ✅ Right Corner Lottie: Syntax Verified */
.right-corner-lottie {
  position: absolute; 
  right: calc(50% - 450px - 160px - 20px);
  
  
  
  
  
  top: 300px;       
  
  width: 160px;    
  height: 160px;   
  z-index: 10;     
}


/* Center Lottie Container Styles */
.lottie-container {
  width: 220px; 
  height: 220px;
  margin: 0 auto 1rem auto;
}

.hero-lottie {
  width: 100%;
  height: 100%;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  margin-bottom: 1.5rem;
  line-height: 1.1;
  color: #1a1a2e;
}

.hero-subtitle {
  font-size: 1.25rem;
  color: #6a6a85;
  margin-bottom: 3rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.hero-actions {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
}

.btn {
  text-decoration: none;
  padding: 0.8rem 2rem;
  border-radius: 4px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  display: inline-flex;
  align-items: center;
}

.primary-cta {
  background-color: #1a1a2e; 
  color: #ffffff;
}

.primary-cta:hover {
  background-color: #33334d;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.secondary-cta {
  background-color: #ffffff; 
  color: #1a1a2e;
  border: 1px solid #c0c0c0;
}

.secondary-cta:hover {
  border-color: #1a1a2e;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}

.arrow {
  margin-left: 0.5rem;
  font-weight: 400;
  font-size: 1.2rem;
}

/* --- Features Section Styles (Three Cards) --- */
.features-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  padding: 3rem 2rem 8rem;
}

.feature-card {
  padding: 2rem;
  text-align: left;
}

.icon svg {
  color: #3f51b5;
  margin-bottom: 1rem;
}

.card-title {
  font-size: 1.35rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
  color: #1a1a2e;
}

.card-description {
  color: #6a6a85;
  line-height: 1.6;
}

/* --- Media Queries for Responsiveness --- */
@media (max-width: 900px) {
  .features-section {
    grid-template-columns: 1fr;
  }
  
  /* Hide both corner Lotties when screen width is 900px or less */
  .corner-lottie, .right-corner-lottie {
    display: none;
  }
}

@media (max-width: 600px) {
  
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-actions {
    flex-direction: column;
    gap: 1rem;
  }

  /* Center Lottie Mobile Styling */
  .lottie-container {
      width: 100px;
      height: 100px;
      margin-bottom: 0.5rem;
  }
  
  /* Adjusted mobile hero padding */
  .hero-section {
    padding: 3rem 1rem 2rem;
  }
}
</style>