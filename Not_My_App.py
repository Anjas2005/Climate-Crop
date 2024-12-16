import streamlit as st
import requests
import pandas as pd
import plotly.express as px

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
    return weather_df

def analyze_crop_impact(avg_temp, total_rainfall):
    """Analyze the impact of weather conditions on crops."""
    if total_rainfall < 50:
        rain_effect = "Low rainfall, irrigation needed."
    elif 50 <= total_rainfall <= 150:
        rain_effect = "Optimal rainfall for most crops."
    else:
        rain_effect = "Excess rainfall, risk of waterlogging."

    if avg_temp < 20:
        temp_effect = "Low temperature, slow growth likely."
    elif 20 <= avg_temp <= 30:
        temp_effect = "Optimal temperature for growth."
    else:
        temp_effect = "High temperature, risk of heat stress."

    return f"Rainfall impact: {rain_effect}\nTemperature impact: {temp_effect}"

def main():
    st.title("Weather Analysis for Agriculture in Bengaluru")

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
            avg_temp = filtered_df[["max_temperature", "min_temperature"]].mean().mean()
            total_rainfall = filtered_df["rainfall"].sum()

            st.subheader("Summary Statistics")
            st.write(f"**Average Temperature:** {avg_temp:.2f} °C")
            st.write(f"**Total Rainfall:** {total_rainfall:.2f} mm")

            # Analyze crop impact
            st.subheader("Impact on Crops")
            impact_analysis = analyze_crop_impact(avg_temp, total_rainfall)
            st.write(impact_analysis)

            # Visualize data
            st.subheader("Visualizations")
            temp_fig = px.line(filtered_df, x="date", y=["max_temperature", "min_temperature"],
                               title="Temperature Over Time",
                               labels={"value": "Temperature (°C)", "variable": "Temperature Type"})
            rain_fig = px.line(filtered_df, x="date", y="rainfall",
                               title="Rainfall Over Time",
                               labels={"rainfall": "Rainfall (mm)"})

            st.plotly_chart(temp_fig)
            st.plotly_chart(rain_fig)
        else:
            st.warning("No data available for the selected date range.")

if __name__ == "__main__":
    main()
