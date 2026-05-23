
import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier
from tqdm import tqdm

DATA_PATH = "nifty500_ohlcv.csv"

def load_data():
    if not os.path.exists(DATA_PATH):
        return None
    df = pd.read_csv(DATA_PATH)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def generate_features(df):
    all_features = []
    # Limit to 10 symbols for better representation in audit
    symbols = df['Symbol'].unique()[:10]
    grouped = df[df['Symbol'].isin(symbols)].groupby('Symbol')

    for sym, group in tqdm(grouped, desc="Processing Audit Data"):
        group = group.sort_values('Date').reset_index(drop=True)
        if len(group) < 100: continue

        close = group['Close']
        volume = group['Volume']

        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-6)
        rsi = 100 - (100 / (1 + rs))

        ema5 = close.ewm(span=5).mean()
        ema_signal = ((close - ema5) / ema5) * 100

        vol_avg = volume.rolling(21).mean()
        vol_ratio = volume / vol_avg.replace(0, 1e-6)

        r_s = close.pct_change(5) * 100
        r_m = close.pct_change(10) * 100
        r_l = close.pct_change(21) * 100

        # 7. Hurst Exponent (Trend persistence)
        hurst = close.rolling(30).apply(lambda x: 0.5 if np.std(x) == 0 else np.polyfit(np.log(range(2, 10)), np.log([np.std(np.subtract(x.values[lag:], x.values[:-lag])) if np.std(np.subtract(x.values[lag:], x.values[:-lag])) > 1e-6 else 1e-6 for lag in range(2, 10)]), 1)[0] if len(x) >= 30 else 0.5)

        # 8. TD Count (Simplified for rolling performance)
        def calc_td_count(x):
            count = 0
            for i in range(0, 9):
                idx = -1 - i
                if len(x) > abs(idx) + 4:
                    if x.iloc[idx] > x.iloc[idx-4]:
                        count += 1
                    else:
                        break
            return count
        td = close.rolling(15).apply(calc_td_count)

        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        squeeze = (bb_std * 4) / bb_mid.replace(0, 1e-6)
        coiling = (close.rolling(20).max() - close.rolling(20).min()) / bb_mid.replace(0, 1e-6)

        future_close = close.shift(-10)
        actual_return = (future_close - close) / close

        temp_df = pd.DataFrame({
            'f1_rsi': rsi,
            'f2_ema': ema_signal,
            'f3_vol': vol_ratio,
            'f4_rs': r_s,
            'f5_rm': r_m,
            'f6_rl': r_l,
            'f7_hurst': hurst.fillna(0.5),
            'f8_td': td.fillna(0),
            'f9_squeeze': squeeze,
            'f10_coiling': coiling,
            'label': (actual_return > 0.03).astype(int),
            'Date': group['Date']
        })

        valid_rows = temp_df[temp_df['Date'] >= "2024-01-01"].dropna()
        all_features.append(valid_rows)

    if not all_features: return None
    return pd.concat(all_features)

def audit_training():
    print("Starting Audit: Feature Importance Calculation")
    df = load_data()
    if df is None:
        print("Error: Could not load data.")
        return

    data = generate_features(df)
    if data is None:
        print("Error: No features generated.")
        return

    feature_cols = ['f1_rsi', 'f2_ema', 'f3_vol', 'f4_rs', 'f5_rm', 'f6_rl', 'f7_hurst', 'f8_td', 'f9_squeeze', 'f10_coiling']
    X = data[feature_cols]
    y = data['label']

    clf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    clf.fit(X, y)

    importances = dict(zip(feature_cols, clf.feature_importances_))
    print("\nFeature Importances (Random Forest):")
    for f in sorted(importances, key=importances.get, reverse=True):
        print(f"{f:12}: {importances[f]:.4f}")

if __name__ == "__main__":
    audit_training()
