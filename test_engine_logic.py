
import pandas as pd
import numpy as np
from engine import WolfPackEngine

def test_engine_metrics():
    # Create some dummy data
    data = {
        'Close': [100 + i + (i % 3) * 2 for i in range(100)],
        'Volume': [1000 + (i % 5) * 100 for i in range(100)],
        'High': [105 + i + (i % 3) * 2 for i in range(100)],
        'Low': [95 + i + (i % 3) * 2 for i in range(100)]
    }
    df = pd.DataFrame(data)
    engine = WolfPackEngine(model_path="v10_model.pkl")

    metrics = engine.calculate_metrics(df)

    if metrics is None:
        print("FAILED: metrics is None")
        return

    print("Calculated Metrics:")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    # Verify RSI manually
    close = df['Close']
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    expected_rsi = 100 - (100 / (1 + (gain / loss.replace(0, 1e-6))))
    expected_rsi_val = float(expected_rsi.iloc[-1])

    assert np.isclose(metrics['rsi'], expected_rsi_val), f"RSI mismatch: {metrics['rsi']} != {expected_rsi_val}"
    print("RSI Verified")

    # Verify TD Count
    # i=1: close[-1] > close[-5] ? 100+99+0=199 vs 100+95+0=195 -> True (1)
    # i=2: close[-2] > close[-6] ? 100+98+2=200 vs 100+94+2=196 -> True (2)
    # ...
    # This loop in engine.py:
    # for i in range(1, 10):
    #     if len(close) > i+4 and float(close.iloc[-i]) > float(close.iloc[-i-4]):
    #         td_count += 1
    #     else:
    #         break

    manual_td = 0
    for i in range(1, 10):
        if len(close) > i+4 and float(close.iloc[-i]) > float(close.iloc[-i-4]):
            manual_td += 1
        else:
            break

    assert metrics['td_count'] == manual_td, f"TD Count mismatch: {metrics['td_count']} != {manual_td}"
    print("TD Count Verified")

if __name__ == "__main__":
    test_engine_metrics()
