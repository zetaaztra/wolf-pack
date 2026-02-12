
import pandas as pd
import numpy as np
import os
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from tqdm import tqdm

# ==========================================
# CONFIGURATION
# ==========================================
# Path to the shared Nifty 500 OHLCV data
DATA_PATH = "nifty500_ohlcv.csv"
MODEL_PATH = "v10_model.pkl"

# Training Hyperparameters
TRAINING_WINDOW_START = "2024-01-01" 
HOLD_DAYS = 10
TARGET_RETURN = 0.03 # 3% gain in 10 days = Success (Label 1)

def load_data():
    if not os.path.exists(DATA_PATH):
        print(f"❌ Data file not found at: {DATA_PATH}")
        print("Please ensure your Alpha_Zeta_Super_Scanner/data folder is intact.")
        return None
    print(f"📂 Loading historical data...")
    df = pd.read_csv(DATA_PATH)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def generate_features(df):
    all_features = []
    grouped = df.groupby('Symbol')
    
    for sym, group in tqdm(grouped, desc="Processing Wolf Brain Data"):
        group = group.sort_values('Date').reset_index(drop=True)
        if len(group) < 100: continue
        
        close = group['Close']
        volume = group['Volume']
        
        # 1. RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-6)
        rsi = 100 - (100 / (1 + rs))
        
        # 2. EMA Signal (f2_ema) - Matches engine.py
        ema5 = close.ewm(span=5).mean()
        ema_signal = ((close - ema5) / ema5) * 100
        
        # 3. Volume Ratio (f3_vol)
        vol_avg = volume.rolling(21).mean()
        vol_ratio = volume / vol_avg.replace(0, 1e-6)
        
        # 4. Returns (f4, f5, f6)
        r_s = close.pct_change(5) * 100
        r_m = close.pct_change(10) * 100
        r_l = close.pct_change(21) * 100
        
        # 9. Squeeze & Coiling (NEW — replaces circular ensemble)
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        squeeze = (bb_std * 4) / bb_mid.replace(0, 1e-6)
        coiling = (close.rolling(20).max() - close.rolling(20).min()) / bb_mid.replace(0, 1e-6)
        
        # 5. Label Generation (Future 10-day return)
        future_close = close.shift(-HOLD_DAYS)
        actual_return = (future_close - close) / close
        
        # Combine into Feature Box
        temp_df = pd.DataFrame({
            'f1_rsi': rsi,
            'f2_ema': ema_signal,
            'f3_vol': vol_ratio,
            'f4_rs': r_s,
            'f5_rm': r_m,
            'f6_rl': r_l,
            'f7_hurst': 0.5,
            'f8_td': 0.0,
            'f9_squeeze': squeeze,
            'f10_coiling': coiling,
            'label': (actual_return > TARGET_RETURN).astype(int),
            'Date': group['Date']
        })
        
        # Filter for Training Window
        mask = (temp_df['Date'] >= TRAINING_WINDOW_START)
        valid_rows = temp_df[mask].dropna()
        all_features.append(valid_rows)
        
    if not all_features: return None
    return pd.concat(all_features)

def train_wolf():
    df = load_data()
    if df is None: return
    
    data = generate_features(df)
    if data is None or data.empty:
        print("❌ Failed to generate training features.")
        return

    print(f"📊 Dataset Size: {len(data)} rows")
    
    feature_cols = ['f1_rsi', 'f2_ema', 'f3_vol', 'f4_rs', 'f5_rm', 'f6_rl', 'f7_hurst', 'f8_td', 'f9_squeeze', 'f10_coiling']
    X = data[feature_cols]
    y = data['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Random Forest Configuration (Conservative to prevent noise-chasing)
    clf = RandomForestClassifier(
        n_estimators=150, 
        max_depth=8, 
        min_samples_split=50,
        random_state=42,
        class_weight="balanced"
    )
    
    print("🧠 Retraining the Wolf Brain...")
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    print("\n✅ RETRAINING COMPLETE")
    print(classification_report(y_test, y_pred))
    
    # Save to local folder
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(clf, f)
    print(f"\n💾 Model Overwritten: {MODEL_PATH}")
    print("🚀 Your Alpha-Wolf Pack Scanner will now use this updated Brain.")

if __name__ == "__main__":
    train_wolf()
