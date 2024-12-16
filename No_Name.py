import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from datetime import datetime, timedelta
import urllib 

def fetch_nasa_power_data(latitude, longitude, start_date, end_date):
    """
    Fetch agricultural and meteorological data from NASA POWER API with robust error handling
    """
    base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    # Convert dates to required format
    start = start_date.strftime("%Y%m%d")
    end = end_date.strftime("%Y%m%d")
    
    # Parameters to fetch
    parameters = [
        "T2M",         # Air temperature at 2 meters
        "RH2M",        # Relative humidity at 2 meters
        "PRECTOTCORR", # Precipitation
        "ALLSKY_SFC_SW_DWN"  # Shortwave solar radiation
    ]
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start": start,
        "end": end,
        "community": "AG",
        "parameters": ",".join(parameters),
        "format": "json"
    }
    
    try:
        # Print out the exact URL and parameters for debugging
        full_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        st.write(f"Requesting URL: {full_url}")
        
        # Make the request
        response = requests.get(base_url, params=params)
        
        # Check if request was successful
        if response.status_code != 200:
            st.error(f"HTTP Error: {response.status_code}")
            st.error(f"Response Content: {response.text}")
            return None
        
        # Try to parse the JSON
        try:
            data = response.json()
        except json.JSONDecodeError as je:
            st.error(f"JSON Decode Error: {je}")
            st.error(f"Response Content: {response.text}")
            return None
        
        # Validate the data structure
        if 'properties' not in data or 'parameter' not in data['properties']:
            st.error("Unexpected data structure")
            st.error(f"Received data: {json.dumps(data, indent=2)}")
            return None
        
        # Process the data
        processed_data = []
        
        # Check the actual structure of the parameters
        st.write("Debug: Available parameters", list(data['properties']['parameter'].keys()))
        
        for date, values in data['properties']['parameter'].items():
            try:
                processed_data.append({
                    'date': datetime.strptime(date, "%Y%m%d"),
                    'temperature': values.get('T2M', None),
                    'humidity': values.get('RH2M', None),
                    'precipitation': values.get('PRECTOTCORR', None),
                    'solar_radiation': values.get('ALLSKY_SFC_SW_DWN', None)
                })
            except Exception as e:
                st.error(f"Error processing date {date}: {e}")
        
        # Convert to DataFrame
        df = pd.DataFrame(processed_data)
        
        # Remove rows with None values
        df = df.dropna()
        
        if df.empty:
            st.error("No valid data could be processed")
            return None
        
        return df
    
    except requests.RequestException as re:
        st.error(f"Request Error: {re}")
        return None
    except Exception as e:
        st.error(f"Unexpected Error: {e}")
        return None

def calculate_rice_crop_health_score(row):
    """
    Calculate rice crop health score with error handling
    """
    try:
        # Rice-specific optimal ranges
        conditions = {
            'temperature': {'min': 20, 'max': 35, 'ideal': 25},
            'humidity': {'min': 60, 'max': 80, 'ideal': 70},
            'precipitation': {'min': 100, 'max': 200, 'ideal': 150},
            'solar_radiation': {'min': 4, 'max': 6, 'ideal': 5}
        }
        
        # Helper function to calculate parameter score
        def calculate_parameter_score(value, param_conditions):
            if value is None:
                return 0
            
            # If outside range, score drops
            if value < param_conditions['min'] or value > param_conditions['max']:
                return max(0, 100 - abs(value - param_conditions['ideal']) * 5)
            
            # Closer to ideal, higher the score
            distance_from_ideal = abs(value - param_conditions['ideal'])
            max_distance = max(
                abs(param_conditions['min'] - param_conditions['ideal']), 
                abs(param_conditions['max'] - param_conditions['ideal'])
            )
            
            # Quadratic scoring
            score = 100 * (1 - (distance_from_ideal / max_distance)**2)
            return max(0, score)
        
        # Calculate scores for each parameter
        scores = {
            'temperature': calculate_parameter_score(row['temperature'], conditions['temperature']),
            'humidity': calculate_parameter_score(row['humidity'], conditions['humidity']),
            'precipitation': calculate_parameter_score(row['precipitation'], conditions['precipitation']),
            'solar_radiation': calculate_parameter_score(row['solar_radiation'], conditions['solar_radiation'])
        }
        
        # Weighted average of scores
        crop_health_score = (
            scores['temperature'] * 0.35 + 
            scores['precipitation'] * 0.3 + 
            scores['humidity'] * 0.2 + 
            scores['solar_radiation'] * 0.15
        )
        
        return crop_health_score
    
    except Exception as e:
        st.error(f"Error calculating crop health score: {e}")
        return None

def main():
    st.title("Rice Crop Health Analysis for Bengaluru")
    
    # Bengaluru Coordinates
    BENGALURU_LAT = 12.9716
    BENGALURU_LON = 77.5946
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", 
                                   value=datetime.now() - timedelta(days=365),
                                   max_value=datetime.now())
    with col2:
        end_date = st.date_input("End Date", 
                                 value=datetime.now(),
                                 max_value=datetime.now())
    
    # Fetch data
    try:
        rice_data = fetch_nasa_power_data(BENGALURU_LAT, BENGALURU_LON, start_date, end_date)
        
        if rice_data is not None and not rice_data.empty:
            # Calculate crop health score
            rice_data['crop_health_score'] = rice_data.apply(calculate_rice_crop_health_score, axis=1)
            
            # Remove any rows where crop health score couldn't be calculated
            rice_data = rice_data.dropna(subset=['crop_health_score'])
            
            if rice_data.empty:
                st.error("No valid crop health scores could be calculated.")
                return
            
            # Summary Statistics
            st.header("Rice Crop Conditions in Bengaluru")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Avg Temperature", f"{rice_data['temperature'].mean():.2f} °C")
            
            with col2:
                st.metric("Total Precipitation", f"{rice_data['precipitation'].sum():.2f} mm")
            
            with col3:
                st.metric("Avg Crop Health Score", f"{rice_data['crop_health_score'].mean():.2f}")
            
            # Visualizations
            st.header("Rice Crop Health Insights")
            
            # Temperature Trend
            temp_fig = px.line(rice_data, x='date', y='temperature', 
                               title='Temperature Trend for Rice Cultivation')
            st.plotly_chart(temp_fig)
            
            # Precipitation Trend
            precip_fig = px.line(rice_data, x='date', y='precipitation', 
                                 title='Precipitation Trend for Rice Fields')
            st.plotly_chart(precip_fig)
            
            # Crop Health Score Trend
            health_fig = px.line(rice_data, x='date', y='crop_health_score', 
                                 title='Rice Crop Health Score Over Time')
            st.plotly_chart(health_fig)
            
            # Downloadable Data
            st.download_button(
                label="Download Rice Crop Data",
                data=rice_data.to_csv(index=False),
                file_name='bengaluru_rice_crop_data.csv',
                mime='text/csv'
            )
        
        else:
            st.error("No data could be retrieved from NASA POWER API.")
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()