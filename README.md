# 🐺 Wolf-Pack Scanner (The Strategy)

## 🚀 Overview
**Wolf-Pack** is the **strategic evolution** of the scanner ecosystem. It introduces the **3-Layer Defense** concept, designed for **"Surgical" precision trading**.

**Best For:**
*   Advanced swing traders.
*   Traders who want "Surgical" entries with high conviction.
*   Understanding the "Armor / Sword / Eyes" philosophy.

---

## 🛡️ The 3-Layer Architecture

### 1. The Armor (Market Health)
*   **Goal:** Protect capital.
*   **Logic:** Checks Nifty 50 vs SMA20 & SMA50.
*   **Verdict:** BULL (Green), CHOP (Yellow), BEAR (Red).

### 2. The Sword (Kimi Score)
*   **Goal:** Identify high-quality setups.
*   **Logic:** 0-100 Score based on 4 Pillars:
    1.  **Quality:** Price > SMA50.
    2.  **Value:** RSI Sweet Spot (40-60).
    3.  **Volatility:** Low volatility premium.
    4.  **Momentum:** Weighted returns.

### 3. The Eyes (V10 AI Model)
*   **Goal:** Predict probability of success.
*   **Logic:** Random Forest Classifier driven by **10 Technical Features**.

---

## 🛠️ Configuration & Usage

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Run the Streamlit Dashboard (Recommended)
```bash
streamlit run app.py
```
*   **Surgical Verdict:** Automatically combines AI + Kimi Score + Market Health.
*   **Red Flags:** See exactly *why* a trade is rejected (e.g., "RSI Overheated", "Low AI Conviction").

### 3. Retrain the Wolf Brain
```bash
python trainer.py
```
*   **New Feature:** Generates `v10_model.pkl` with Squeeze + Coiling logic.

---

## ⚠️ Important Notes (Feb 2025 Update)

### 🔴 Critical Fixes Implemented
*   **Fixed AI Features:** Removed circular dependency. Now uses Bollinger Squeeze + Price Coiling.
*   **Fixed Engine:** Now calculates ALL 10 required features correctly.
*   **Fixed Scaling:** Kimi momentum score standardized to prevent capping strong movers.

### 📉 Score Interpretation
*   **Surgical Entry:** High AI Prob (>70%) + Strong Kimi Score (>20) + Safe Market.
*   **Speculative Rebound:** Allowed in Aggressive Mode if Price < SMA50 but Momentum is high.

---

## 📜 License
Privately developed for high-probability swing trading.
