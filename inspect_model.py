import pickle
import sys
import os

model_path = r"c:\Users\hp\Desktop\Scanners\wolf-pack-main\v10_model.pkl"

if not os.path.exists(model_path):
    print("Model file not found!")
    sys.exit(1)

try:
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    if hasattr(model, 'feature_names_in_'):
        print("Model expects these features:")
        print(model.feature_names_in_)
    else:
        print("Model does not have feature_names_in_ attribute.")
        print(f"Model type: {type(model)}")

except Exception as e:
    print(f"Error loading model: {e}")
