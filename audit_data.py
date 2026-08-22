
import pandas as pd
import os

def audit_data_integrity():
    DATA_PATH = "nifty500_ohlcv.csv"
    if not os.path.exists(DATA_PATH):
        print("Data file not found")
        return

    df = pd.read_csv(DATA_PATH)
    print(f"Total Rows: {len(df)}")
    print(f"Missing Values:\n{df.isnull().sum()}")

    # Check for duplicate Symbol/Date pairs
    duplicates = df.duplicated(subset=['Symbol', 'Date']).sum()
    print(f"Duplicate Symbol/Date pairs: {duplicates}")

    # Check for zero Volume or Price
    zero_price = (df['Close'] <= 0).sum()
    zero_volume = (df['Volume'] < 0).sum()
    print(f"Zero/Negative Price: {zero_price}")
    print(f"Negative Volume: {zero_volume}")

    # Check date range
    df['Date'] = pd.to_datetime(df['Date'])
    print(f"Date Range: {df['Date'].min()} to {df['Date'].max()}")

if __name__ == "__main__":
    audit_data_integrity()
