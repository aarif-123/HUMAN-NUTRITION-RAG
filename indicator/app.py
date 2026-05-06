# ================= BTC AI ENGINE (PRO VERSION) =================
# pip install yfinance pandas scikit-learn joblib numpy python-dotenv

import yfinance as yf
import pandas as pd
import numpy as np
import joblib
import os
from dotenv import load_dotenv

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ================= LOAD ENV =================
load_dotenv()

API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

# ================= FETCH DATA =================
def fetch_btc_data():
    print("Fetching 10 years BTC data...")

    df = yf.download("BTC-USD", period="10y", interval="1d")

    df.reset_index(inplace=True)

    # FIX: flatten column
    df["close"] = df["Close"]

    print("Data fetched:", df.shape)
    return df

# ================= FEATURES =================
def add_features(df):
    print("Adding indicators...")

    df["SMA_10"] = df["close"].rolling(10).mean()
    df["EMA_10"] = df["close"].ewm(span=10).mean()

    delta = df["close"].diff()

    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    loss = loss.replace(0, 1e-10)
    rs = gain / loss

    df["RSI"] = 100 - (100 / (1 + rs))

    df["returns"] = df["close"].pct_change()

    return df.dropna()

# ================= TRAIN + EVALUATE =================
def train_and_evaluate(df):
    print("Training + evaluating model...")

    df["target"] = df["close"].shift(-1)
    df = df.dropna()

    features = ["SMA_10", "EMA_10", "RSI", "returns"]

    X = df[features]
    y = df["target"]

    # ===== TIME-BASED SPLIT =====
    split = int(len(df) * 0.8)

    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        random_state=42
    )

    model.fit(X_train, y_train)

    # ===== PREDICTIONS =====
    y_pred = model.predict(X_test)

    # ===== METRICS =====
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    # ===== DIRECTIONAL ACCURACY =====
    direction_true = np.sign(y_test.values - X_test["SMA_10"].values)
    direction_pred = np.sign(y_pred - X_test["SMA_10"].values)

    directional_accuracy = np.mean(direction_true == direction_pred)

    print("\n===== MODEL PERFORMANCE =====")
    print(f"MAE: {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R2 Score: {r2:.4f}")
    print(f"Directional Accuracy: {directional_accuracy:.2%}")

    return model, df

# ================= REALTIME SIMULATION =================
def realtime_simulation(df, model):
    print("\nRunning realtime simulation...")

    features = ["SMA_10", "EMA_10", "RSI", "returns"]

    correct = 0
    total = 0

    for i in range(len(df) - 1):
        row = df.iloc[i:i+1]
        next_actual = float(df["close"].iloc[i+1])
        current_price = float(row["close"].values[0])

        pred = float(model.predict(row[features])[0])

        actual_dir = np.sign(next_actual - current_price)
        pred_dir = np.sign(pred - current_price)

        # FIX: ensure scalar comparison
        if actual_dir == pred_dir:
            correct += 1

        total += 1

    acc = correct / total
    print(f"Realtime Direction Accuracy: {acc:.2%}")
# ================= SAVE =================
def save_model(model):
    joblib.dump(model, "btc_model.pkl")
    print("Model saved as btc_model.pkl")

# ================= PREDICT =================
def predict_next(df, model):
    latest = df.tail(1)
    features = latest[["SMA_10", "EMA_10", "RSI", "returns"]]

    prediction = model.predict(features)[0]

    return prediction

# ================= MAIN =================
if __name__ == "__main__":
    df = fetch_btc_data()
    df = add_features(df)

    model, df = train_and_evaluate(df)

    realtime_simulation(df, model)

    save_model(model)

    pred = predict_next(df, model)

    print("\n====== RESULT ======")
    print("Current Price:", df["close"].iloc[-1])
    print("Predicted Next Price:", pred)