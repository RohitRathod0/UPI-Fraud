import xgboost as xgb
print(f"XGBoost version: {xgb.__version__}")
print("Note: XGBoost 2.0+ removed early_stopping_rounds from fit()")
print("Solution: Remove that parameter from model training code")
