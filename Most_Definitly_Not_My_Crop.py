import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np

# Open-Meteo API Endpoint
API_URL = "https://api.open-meteo.com/v1/forecast"

@st.cache_data
def fetch_weather_data(lat, lon):
    """Fetch weather data from Open-Meteo API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Asia/Kolkata",
    }
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def process_weather_data(data):
    """Process Open-Meteo API data into a DataFrame."""
    dates = data["daily"]["time"]
    max_temps = data["daily"]["temperature_2m_max"]
    min_temps = data["daily"]["temperature_2m_min"]
    rainfall = data["daily"]["precipitation_sum"]
    
    weather_df = pd.DataFrame({
        "date": pd.to_datetime(dates),
        "max_temperature": max_temps,
        "min_temperature": min_temps,
        "rainfall": rainfall,
    })
    weather_df['avg_temperature'] = (weather_df['max_temperature'] + weather_df['min_temperature']) / 2
    return weather_df

def analyze_rice_crop_health(temperature, rainfall):
    """Generate rice crop health score based on temperature and rainfall."""
    # Rice optimal temperature range: 20°C - 30°C and rainfall around 100-150 mm
    temp_score = max(0, 100 - abs(temperature - 25) * 3)
    rain_score = max(0, 100 - abs(rainfall - 125) * 0.8)
    crop_health_score = (temp_score * 0.6 + rain_score * 0.4)  # Weighted average
    return crop_health_score

def predict_future_temperatures(df):
    """Predict future average temperatures using Linear Regression."""
    # Prepare the data for regression
    df = df.reset_index(drop=True)
    df['days'] = (df['date'] - df['date'].min()).dt.days
    X = df[['days']]
    y = df['avg_temperature']
    model = LinearRegression()
    model.fit(X, y)

    # Predict for the next 30 days
    future_days = np.arange(df['days'].max() + 1, df['days'].max() + 31).reshape(-1, 1)
    future_dates = [df['date'].max() + pd.Timedelta(days=i) for i in range(1, 31)]
    future_temps = model.predict(future_days)

    future_df = pd.DataFrame({
        "date": future_dates,
        "predicted_avg_temperature": future_temps
    })
    return future_df

def main():
    st.title("Weather and Rice Crop Health Prediction in Bengaluru")

    # Define Bengaluru coordinates
    latitude = 12.9716
    longitude = 77.5946

    # Fetch data from Open-Meteo
    weather_data = fetch_weather_data(latitude, longitude)

    if weather_data:
        weather_df = process_weather_data(weather_data)

        # Display dataset preview
        st.subheader("Weather Data")
        st.write("Preview of weather data:")
        st.dataframe(weather_df.head())

        # Filter dataset for user-specified date range
        st.subheader("Filter Data by Date Range")
        start_date = st.date_input("Start Date", value=weather_df["date"].min())
        end_date = st.date_input("End Date", value=weather_df["date"].max())
        filtered_df = weather_df[(weather_df["date"] >= pd.Timestamp(start_date)) & (weather_df["date"] <= pd.Timestamp(end_date))]

        if not filtered_df.empty:
            # Display filtered data
            st.write("Filtered Data:")
            st.dataframe(filtered_df)

            # Calculate average temperature and total rainfall
            avg_temp = filtered_df["avg_temperature"].mean()
            total_rainfall = filtered_df["rainfall"].sum()

            st.subheader("Summary Statistics")
            st.write(f"**Average Temperature:** {avg_temp:.2f} °C")
            st.write(f"**Total Rainfall:** {total_rainfall:.2f} mm")

            # Analyze rice crop health
            st.subheader("Rice Crop Health Analysis")
            rice_crop_health = analyze_rice_crop_health(avg_temp, total_rainfall)
            st.write(f"**Rice Crop Health Score:** {rice_crop_health:.2f} (Scale: 0-100)")

            # Predict future temperatures
            st.subheader("Temperature Predictions")
            future_temps_df = predict_future_temperatures(weather_df)
            st.write("Predicted Average Temperatures for the Next 30 Days:")
            st.dataframe(future_temps_df)

            # Visualize data
            st.subheader("Visualizations")
            temp_fig = px.line(filtered_df, x="date", y=["max_temperature", "min_temperature", "avg_temperature"],
                               title="Temperature Trends",
                               labels={"value": "Temperature (°C)", "variable": "Temperature Type"})
            rain_fig = px.line(filtered_df, x="date", y="rainfall",
                               title="Rainfall Trends",
                               labels={"rainfall": "Rainfall (mm)"})
            pred_fig = px.line(future_temps_df, x="date", y="predicted_avg_temperature",
                               title="Predicted Average Temperatures",
                               labels={"predicted_avg_temperature": "Temperature (°C)"})

            st.plotly_chart(temp_fig)
            st.plotly_chart(rain_fig)
            st.plotly_chart(pred_fig)

            # Rice Crop Health Graph
            st.subheader("Rice Crop Health Prediction Graph")
            health_fig = px.line(filtered_df, x="date", y=filtered_df["avg_temperature"].apply(lambda t: analyze_rice_crop_health(t, total_rainfall)),
                                 title="Rice Crop Health Over Time",
                                 labels={"y": "Crop Health Score (0-100)", "date": "Date"})
            st.plotly_chart(health_fig)

        else:
            st.warning("No data available for the selected date range.")

if __name__ == "__main__":
    main()
