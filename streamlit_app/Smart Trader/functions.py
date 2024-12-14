import yfinance as yf
import numpy as np
import pandas as pd
from datetime import date, timedelta
from sklearn.preprocessing import MinMaxScaler

def predict_multiple_days(model, scaler, recent_data, target_date, data_index, business_days=5):
    """
    Predict prices for a specific day and subsequent business days.
    :param model: Trained LSTM model
    :param scaler: MinMaxScaler used for normalization
    :param recent_data: Most recent `look_back` days of scaled data with 4 features
    :param target_date: The future date to predict (YYYY-MM-DD)
    :param data_index: The index of dates in the dataset
    :param business_days: Number of business days to predict after the target date
    :return: DataFrame with predicted Open, High, Low, Close prices for the specified period
    """
    from datetime import datetime, timedelta
    import pandas as pd

    # Ensure recent_data has the correct shape
    if recent_data.shape[1] != 4:
        raise ValueError(f"Expected 4 features (Open, High, Low, Close), but got {recent_data.shape[1]} features.")

    # Initialize input and predictions
    current_input = recent_data.reshape(1, recent_data.shape[0], recent_data.shape[1])  # (1, look_back, 4)
    predictions = []
    dates = []

    # Start with the target date
    predicted_date = datetime.strptime(target_date, "%Y-%m-%d")

    # Predict for the target date and subsequent business days
    for step in range(business_days):
        print(f"Predicting day {step + 1}")
        prediction = model.predict(current_input, verbose=0)

        # Denormalize the prediction
        denormalized_prediction = scaler.inverse_transform(prediction)
        predictions.append(denormalized_prediction[0])
        dates.append(predicted_date)

        # Update the sliding window
        new_input_row = np.vstack([current_input[0, 1:], prediction])  # Slide the input window
        current_input = new_input_row.reshape(1, current_input.shape[1], current_input.shape[2])

        # Move to the next business day
        predicted_date += timedelta(days=1)
        while predicted_date.weekday() >= 5:  # Skip weekends (5=Saturday, 6=Sunday)
            predicted_date += timedelta(days=1)

    # Create DataFrame for predictions
    df_predictions = pd.DataFrame(predictions, columns=['Open', 'High', 'Low', 'Close'])
    df_predictions['Date'] = dates
    df_predictions.set_index('Date', inplace=True)

    return df_predictions

# Function to filter data up to a specific date
def filter_data_by_date(data, target_date):
    """
    Filter the dataset to include only data up to the target date.

    :param data: Full historical stock price DataFrame.
    :param target_date: Target date as a string (e.g., '2024-12-01').
    :return: Filtered dataset.
    """
    target_date = pd.to_datetime(target_date)
    filtered_df = data[data.index <= target_date]
    if len(filtered_df) < 60:
        raise ValueError("Not enough data available before the target date to make predictions.")
    return filtered_df

# Function to load the LSTM model, and predict a trading strategy
def calculate_trading_strategy(predicted_open_price, current_open_price):
    """
    Calculate trading strategy (BULLISH, BEARISH, IDLE) based on predicted opening prices.

    Args:
        predicted_open_price (float): Predicted opening price for the next day.
        current_open_price (float): Current open price.

    Returns:
        String: Trading action for the day ("BULLISH", "BEARISH", "IDLE").
    """
    # Calculate the expected return for NVDA
    nvda_expected_return = (predicted_open_price - current_open_price) / current_open_price

    # Calculate the expected return for NVDQ (T-Rex 2X inverse ETF)
    nvdq_expected_return = -2 * nvda_expected_return

    # Compare the expected returns to determine the trading strategy
    if nvda_expected_return == nvdq_expected_return:
        return "IDLE"
    elif nvda_expected_return > nvdq_expected_return:
        return "BULLISH"
    else:
        return "BEARISH"

# Function to generate trading strategy for the next 5 days
def generate_trading_strategy(predicted_open_prices, current_open_price):
    """
    Generate trading strategy for the next 5 days based on predicted opening prices.

    Args:
        predicted_open_prices (list): Predicted opening prices for the next 5 days.
        current_open_price (float): Current open price.

    Returns:
        List of Strings: List of trading actions for the next 5 days.
    """
    strategies = []

    for day in range(5):
        # Calculate the trading strategy for the current day
        action = calculate_trading_strategy(predicted_open_prices[day], current_open_price)
        strategies.append(action)

        # Update current_open_price to the predicted opening price for the next day
        current_open_price = predicted_open_prices[day]

    return strategies