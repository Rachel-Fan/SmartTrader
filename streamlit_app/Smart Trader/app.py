from flask import Flask, render_template, request, jsonify
from functions import *
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import date, timedelta
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/test')
def test():
    return "Hello, World!"

@app.route('/submit-date', methods=['POST'])
def submit_date():
    # Extract the date from the request payload
    selected_date = request.json.get('date')
    if not selected_date:
        return jsonify({"error": "Date not provided in the request."}), 400

    print(f"Received date: {selected_date}")

    # Define parameters for historical data download
    ticker = "NVDA"
    start_date = "2019-01-01"
    end_date = "2024-12-01"

    try:
        # Download historical price data from Yahoo Finance
        data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)
        if data.empty:
            return jsonify({"error": "No data retrieved from Yahoo Finance."}), 500
        
        # Flatten the column names to remove the 'Ticker' level
        data.columns = data.columns.get_level_values(0)
        data.index = pd.to_datetime(data.index)
        data.columns = ['Adj Close','Close','High','Low','Open','Volume']
        
        # get data up to the selected date
        data = filter_data_by_date(data, selected_date)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch data: {str(e)}"}), 500

    try:
        # Extract numeric values
        features = data[['Open', 'High', 'Low', 'Close']].values

        # Normalize the features
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_features = scaler.fit_transform(features)
    except KeyError:
        return jsonify({"error": "Closing price data is missing from the dataset."}), 500

    try:
        # Load the pre-trained model
        model = load_model('model/best_lstm_multitarget3.keras')
        
        look_back = 60
        # Check if enough historical data is available
        if len(data) < look_back:
            raise ValueError("Not enough historical data to make predictions.")
    except Exception as e:
        return jsonify({"error": f"Failed to load the model: {str(e)}"}), 500

    try:
        # Use the last `look_back` days from the dataset
        input_data = scaled_features[-look_back:]
        input_data = input_data.reshape(1, look_back, input_data.shape[1])  # Reshape to match model input shape
        
        # Ensure recent_data includes the last 60 days with 4 features
        recent_data = scaled_features[-look_back:, :4]
        
        # Predict prices for the next 5 business days
        predictions = predict_multiple_days(model, scaler, recent_data, selected_date, data.index, business_days=6)
        predicted_open_prices_6_days = predictions['Open'].tolist()
        if not predicted_open_prices_6_days:
            return jsonify({"error": "Failed to generate predictions."}), 500

        print("Predicted Prices for the Next 5 Days:")
        for i, price in enumerate(predicted_open_prices_6_days, 1):
            print(f"Day {i}: {price:.2f} USD")
    except Exception as e:
        return jsonify({"error": f"Prediction error: {str(e)}"}), 500

    try:
        # Generate trading strategy based on predictions
        current_open_price = predicted_open_prices_6_days[0]
        trading_strategy = generate_trading_strategy(predicted_open_prices_6_days[1:], current_open_price)
        print("Trading Strategy for the next 5 days:", trading_strategy)
    except Exception as e:
        return jsonify({"error": f"Failed to generate trading strategy: {str(e)}"}), 500
    
    # calculate the highest price in the next 5 days
    highest_prices = max(predictions["High"].tolist()[1:])
    print(f"The highest price in the next 5 days: {highest_prices:.2f} USD")
    # calculate the lowest price in the next 5 days
    lowest_prices = min(predictions["Low"].tolist()[1:])
    print(f"The lowest price in the next 5 days: {lowest_prices:.2f} USD")
    # calculate the average price in the next 5 days
    average_price = np.mean(predicted_open_prices_6_days[1:])
    print(f"The average price in the next 5 days: {average_price:.2f} USD")

    # Send the trading strategy, and next five business days back to the frontend
    response_data = {
        "trading_strategy": trading_strategy,
        "next_five_business_days": predictions.index.tolist()[1:],
        "highest_price": highest_prices,
        "lowest_price": lowest_prices,
        "average_price": average_price
    }
    return jsonify(response_data), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
