
import pandas as pd
import numpy as np
import yfinance as yf
import pickle
import os

class WolfPackEngine:
    def __init__(self, model_path="v10_model.pkl"):
        self.model = self._load_model(model_path)
        
    def _load_model(self, path):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return pickle.load(f)
        return None

    def get_market_health(self):
        """Alpha-Kimi-3 logic: Market Armor"""
        try:
            nifty = yf.download('^NSEI', period='100d', progress=False, auto_adjust=True)
            if nifty.empty: return "UNKNOWN", "⚪"
            if isinstance(nifty.columns, pd.MultiIndex): nifty.columns = nifty.columns.get_level_values(0)
            close = nifty['Close']
            sma20 = close.rolling(20).mean().iloc[-1]
            sma50 = close.rolling(50).mean().iloc[-1]
            curr = close.iloc[-1]
            
            if curr > sma20 and curr > sma50: return "BULL (Safe to Hunt)", "🟢"
            if curr < sma20 and curr < sma50: return "BEAR (High Risk)", "🔴"
            return "CHOP (Be Cautious)", "🟡"
        except:
            return "UNKNOWN", "⚪"

    def calculate_metrics(self, df):
        """Consolidated technical core with NaN-Safety — Full Feature Set"""
        if len(df) < 100: return None # Require enough data
        
        close = df['Close']
        vol = df['Volume']
        
        if isinstance(close, pd.DataFrame): close = close.iloc[:, 0]
        if isinstance(vol, pd.DataFrame): vol = vol.iloc[:, 0]
        
        close = close.ffill().dropna().astype(float)
        vol = vol.ffill().dropna().astype(float)
        
        if len(close) < 100: return None
        
        # 1. RSI (f1_rsi)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / loss.replace(0, 1e-6))))
        
        # 2. EMA Signal (f2_ema)
        ema5 = close.ewm(span=5).mean()
        ema_signal = ((close - ema5) / ema5) * 100
        
        # 3. Volume Ratio (f3_vol)
        vol_ratio = vol / vol.rolling(21).mean().replace(0, 1e-6)
        
        # 4. Returns (f4, f5, f6)
        r_s = close.pct_change(5) * 100
        r_m = close.pct_change(10) * 100
        r_l = close.pct_change(21) * 100
        r_3m = (close / close.shift(63) - 1) * 100 # For Kimi Score
        
        # 5. Volatility
        returns = close.pct_change().dropna()
        short_vol = float(returns.iloc[-5:].std() * np.sqrt(252) * 100) if len(returns) > 5 else 10.0
        medium_vol = float(returns.iloc[-10:].std() * np.sqrt(252) * 100) if len(returns) > 10 else 10.0
        
        # 6. Squeeze & Coiling (NEW — replaces circular ensemble)
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        squeeze = (bb_std * 4) / bb_mid.replace(0, 1e-6)
        coiling = (close.rolling(20).max() - close.rolling(20).min()) / bb_mid.replace(0, 1e-6)
        
        # 7. Hurst Exponent (Trend persistence)
        hurst = 0.5
        try:
            ts_clean = close.dropna()
            if len(ts_clean) >= 20:
                lags = range(2, 20)
                tau = [np.std(np.subtract(ts_clean.values[lag:], ts_clean.values[:-lag])) for lag in lags]
                hurst = np.polyfit(np.log(list(lags)), np.log(tau), 1)[0]
        except:
            pass
        
        # 8. TD Count (Exhaustion)
        td_count = 0
        for i in range(1, 10):
            if len(close) > i+4 and float(close.iloc[-i]) > float(close.iloc[-i-4]):
                td_count += 1
            else:
                break
        
        # 9. ATR
        atr = 1.0
        try:
            if 'High' in df.columns and 'Low' in df.columns:
                high = df['High'].iloc[:, 0] if isinstance(df['High'], pd.DataFrame) else df['High']
                low = df['Low'].iloc[:, 0] if isinstance(df['Low'], pd.DataFrame) else df['Low']
                tr1 = high - low
                tr2 = abs(high - close.shift())
                tr3 = abs(low - close.shift())
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr = float(tr.rolling(14).mean().iloc[-1])
        except:
            pass
        
        # Trend & Liquidity
        sma50 = close.rolling(50).mean()
        avg_turnover = (close * vol).rolling(20).mean()
        
        try:
            return {
                'price': float(close.iloc[-1]),
                'rsi': float(rsi.iloc[-1]),
                'ema_signal': float(ema_signal.iloc[-1]),
                'vol_ratio': float(vol_ratio.iloc[-1]),
                'r_s': float(r_s.iloc[-1]),
                'r_m': float(r_m.iloc[-1]),
                'r_l': float(r_l.iloc[-1]),
                'r_3m': float(r_3m.iloc[-1]) if not np.isnan(r_3m.iloc[-1]) else 0.0,
                'short_vol': short_vol,
                'medium_vol': medium_vol,
                'atr': atr,
                'squeeze': float(squeeze.iloc[-1]),
                'coiling': float(coiling.iloc[-1]),
                'hurst': hurst,
                'td_count': td_count,
                'turnover_m': float(avg_turnover.iloc[-1] / 1e6),
                'sma50': float(sma50.iloc[-1])
            }
        except:
            return None

    def get_kimi_score(self, metrics, timeframe="1-2 Weeks"):
        """The Sword: Quality + Momentum (Timeframe-Aware)
        Computes a 0-100 score from four computed pillars:
        - Quality: Price strength vs SMA50
        - Value: RSI-based mean-reversion signal (mid-RSI is ideal)
        - Volatility: Lower is better (stability premium)
        - Momentum: Weighted short/medium/long returns
        """
        if metrics is None: return 0.0
        
        # Momentum pillar: timeframe-aware weighting of returns
        if "3-7 Days" in timeframe:
            m_score = (metrics['r_s']*0.5 + metrics['r_m']*0.3 + metrics['r_l']*0.2)
        elif "1 Month" in timeframe:
            m_score = (metrics['r_s']*0.1 + metrics['r_m']*0.3 + metrics['r_l']*0.6)
        else:
            m_score = (metrics['r_s']*0.3 + metrics['r_m']*0.4 + metrics['r_l']*0.3)
        
        # Quality pillar: how far above SMA50 (0-10 scale)
        sma50_pct = ((metrics['price'] / metrics['sma50']) - 1) * 100 if metrics['sma50'] > 0 else 0
        q_score = min(10.0, max(0.0, sma50_pct))  # 0-10, capped
        
        # Value pillar: RSI sweet spot (RSI 40-60 scores highest, overbought/oversold penalized)
        rsi = metrics['rsi']
        if 40 <= rsi <= 60:
            v_score = 10.0
        elif 30 <= rsi < 40 or 60 < rsi <= 70:
            v_score = 7.0
        elif rsi < 30:
            v_score = 4.0  # Oversold — risky
        else:
            v_score = 2.0  # Overbought — very risky
        
        # Volatility pillar: lower vol_ratio = more stable (invert, 0-10 scale)
        vol_ratio = metrics.get('vol_ratio', 1.0)
        vol_score = min(10.0, max(0.0, 10.0 - abs(vol_ratio - 1.0) * 5.0))
        
        # Combine all four pillars equally (each 0-10), scale to 0-100
        m_scaled = min(10.0, max(0.0, m_score / 2.0))  # /2.0: takes ~20% return to max out
        total_score = (q_score + v_score + vol_score + m_scaled) * 2.5  # 4 pillars × 10 max × 2.5 = 100 max
        
        return round(max(0.0, min(100.0, total_score)), 2)

    def get_ai_prob(self, metrics):
        """The Eyes: V10 Random Forest (Improved Feature Set)"""
        if self.model is None or metrics is None: return 0.0
        
        try:
            # IMPROVED: Uses squeeze/coiling instead of circular ensemble
            feat_dict = {
                'f1_rsi': [float(metrics.get('rsi', 0))],
                'f2_ema': [float(metrics.get('ema_signal', 0))],
                'f3_vol': [float(metrics.get('vol_ratio', 0))],
                'f4_rs': [float(metrics.get('r_s', 0))],
                'f5_rm': [float(metrics.get('r_m', 0))],
                'f6_rl': [float(metrics.get('r_l', 0))],
                'f7_hurst': [float(metrics.get('hurst', 0.5))],
                'f8_td': [float(metrics.get('td_count', 0))],
                'f9_ensemble': [float(metrics.get('squeeze', 0))],
                'f24_fundamental': [float(metrics.get('coiling', 0))]
            }
            
            X = pd.DataFrame(feat_dict).fillna(0)
            
            prob = self.model.predict_proba(X)[0][1]
            return round(float(prob), 3)
            
        except Exception as e:
            # Diagnostics console print for user to copy/paste
            print(f"⚠️ AI Calculation Blocked: {e}")
            return 0.0

    def get_surgical_verdict(self, metrics, ai_prob, kimi_score, mode="Turbo", qty=0, timeframe="1-2 Weeks"):
        """Surgical Execution Guard - Timeframe Aware"""
        if metrics is None: return False, "Incomplete Data"
        reasons = []
        is_safe = True
        
        # AI Conviction threshold based on timeframe
        # Aggressive needs less proof (0.60), Conservative needs more (0.80)
        if "3-7 Days" in timeframe:
            ai_threshold = 0.60
        elif "1 Month" in timeframe:
            ai_threshold = 0.80
        else:
            ai_threshold = 0.70
            
        # 1. AI Threshold Check
        if ai_prob < ai_threshold:
            reasons.append(f"Low AI Conviction (<{int(ai_threshold*100)}%)")
            is_safe = False
            
        # 2. Trend Guard (Bypassable in Aggressive mode for strong bounces)
        if metrics['price'] < metrics['sma50']:
            # If Aggressive AND High AI AND Strong short-term bounce (>2%)
            if "3-7 Days" in timeframe and ai_prob >= 0.60 and metrics.get('r_s', 0) > 2.0:
                reasons.append("REBOUND SPECULATION (Below SMA50)")
                # We do NOT set is_safe = False here in Aggressive mode for rebounds
            else:
                reasons.append("Price below SMA50")
                is_safe = False
            
        # 3. RSI Overheat
        if metrics['rsi'] > 70:
            reasons.append("RSI Overheated (Avoid Chase)")
            is_safe = False
            
        # 4. Score Check - Timeframe Adjusted
        min_score = 15.0 if "3-7 Days" in timeframe else 20.0
        
        if mode == "Defensive" and kimi_score < min_score:
            reasons.append(f"Low Multi-Pillar Score (<{min_score})")
            is_safe = False

        # 5. Liquidity Guard (1% ADV Rule)
        adv_20_shares = (metrics['turnover_m'] * 1e6) / metrics['price']
        if qty > (adv_20_shares * 0.01):
            reasons.append("Thin Liquidity (Order > 1% ADV)")
            is_safe = False
            
        return is_safe, ", ".join(reasons) if reasons else "SURGICAL ENTRY"
