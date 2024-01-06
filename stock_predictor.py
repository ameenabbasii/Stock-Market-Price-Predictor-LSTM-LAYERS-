import datetime as dt
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, Dense
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display

# Function to preprocess and scale the data
def preprocess_data(data, prediction_days):
    if data.empty:
        raise ValueError("Empty dataset. Please check the data.")
    
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data['Close'].values.reshape(-1, 1))

    x_train, y_train = [], []
    for x in range(prediction_days, len(scaled_data)):
        x_train.append(scaled_data[x - prediction_days: x, 0])
        y_train.append(scaled_data[x, 0])

    x_train, y_train = np.array(x_train), np.array(y_train)
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

    return x_train, y_train, scaler

# Function to create and train the LSTM model
def create_and_train_model(x_train, y_train, epochs, batch_size, loading_bar):
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50, return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50))
    model.add(Dropout(0.2))
    model.add(Dense(units=1))
    model.compile(optimizer='adam', loss='mean_squared_error')

    loading_bar.max = epochs

    for epoch in range(epochs):
        model.fit(x_train, y_train, epochs=1, batch_size=batch_size, verbose=0)
        loading_bar.value = epoch + 1

    return model

# Function to predict stock prices
def predict_stock_prices(model, data, scaler, prediction_days):
    model_inputs = data['Close'].values.reshape(-1, 1)
    model_inputs = scaler.transform(model_inputs)

    x_test = []
    for x in range(prediction_days, len(model_inputs)):
        x_test.append(model_inputs[x - prediction_days:x, 0])

    x_test = np.array(x_test)
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

    predicted_prices = model.predict(x_test)
    predicted_prices = scaler.inverse_transform(predicted_prices)

    return predicted_prices

# Function to save the plot as an image
def save_plot_as_image(actual_prices, predicted_prices, company):
    plt.plot(actual_prices, color="black", label=f"Actual {company} Prices")
    plt.plot(predicted_prices, color="green", label=f"Predicted {company} Prices")
    plt.title(f"{company} Share Prices")
    plt.xlabel('Time')
    plt.ylabel(f"{company} Share Price")
    plt.legend()

    # Save the plot as an image file
    plt.savefig(f"{company}_stock_prediction.png")
    plt.close()  # Close the plot to avoid displaying it interactively

# Function to visualize actual and predicted prices
def plot_stock_prices(actual_prices, predicted_prices, company):
    plt.plot(actual_prices, color="black", label=f"Actual {company} Prices")
    plt.plot(predicted_prices, color="green", label=f"Predicted {company} Prices")
    plt.title(f"{company} Share Prices")
    plt.xlabel('Time')
    plt.ylabel(f"{company} Share Price")
    plt.legend()

    # Display the plot using the IPython display function
    display(plt.gcf())

# Function to fetch data, train model, and plot graph
def process_company(widget):
    company = entry_company.value
    prediction_days = entry_prediction_days.value
    epochs = entry_epochs.value
    batch_size = entry_batch_size.value
    start_date = '2010-01-01'
    end_date_training = '2022-01-01'
    end_date_testing = dt.datetime.now().strftime('%Y-%m-%d')

    try:
        # Download and preprocess training data
        data_training = yf.download(company, start=start_date, end=end_date_training)
        x_train, y_train, scaler = preprocess_data(data_training, prediction_days)

        # Create loading bar widget
        loading_bar = widgets.IntProgress(
            value=0,
            min=0,
            max=epochs,
            description='Training:',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='50%')
        )

        # Display loading bar
        display(loading_bar)

        # Create and train the LSTM model
        model = create_and_train_model(x_train, y_train, epochs, batch_size, loading_bar)

        # Download and preprocess testing data
        data_testing = yf.download(company, start=end_date_training, end=end_date_testing)

        if data_testing.empty:
            raise ValueError("Empty testing dataset. Please check the data.")
    except Exception as e:
        result_label.value = f"Error: {e}"

entry_company = widgets.Text(description="Enter Company:")
entry_prediction_days = widgets.IntText(description="Enter Prediction Days:")
entry_epochs = widgets.IntText(description="Enter Epochs:")
entry_batch_size = widgets.IntText(description="Enter Batch Size:")
btn_process = widgets.Button(description="Process Company")
result_label = widgets.Label()

# Assign the callback function to the button
btn_process.on_click(process_company)

# Display widgets
display(entry_company)
display(entry_prediction_days)
display(entry_epochs)
display(entry_batch_size)
display(btn_process)
display(result_label)

