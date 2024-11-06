import os
import requests
import geopandas as gpd
from shapely.geometry import LineString
from datetime import datetime

# Function to get traffic flow data from HERE API
def get_traffic_flow(bbox, api_key):
    url = f"https://data.traffic.hereapi.com/v7/flow"
    params = {
        'in': f'bbox:{bbox}',
        'locationReferencing': 'shape',
        'advancedFeatures': 'deepCoverage',
        'apiKey': api_key
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

# Function to parse the data and create a GeoDataFrame
def parse_traffic_data(data):
    roads = []
    speeds = []
    
    for result in data['results']:
        location = result['location']
        shape = location['shape']['links']
        
        for link in shape:
            points = link['points']
            line = LineString([(point['lng'], point['lat']) for point in points])
            
            # Check if currentFlow exists and has speed data
            if 'currentFlow' in result and 'speed' in result['currentFlow']:
                speed = result['currentFlow']['speedUncapped']
                speed = speed * 3.6  # Convert from m/s to km/h
            else:
                speed = None  # Assign None if speed data is missing
                
            roads.append(line)
            speeds.append(speed)
    
    # Create a GeoDataFrame with speed as an attribute
    gdf = gpd.GeoDataFrame({'geometry': roads, 'speed': speeds}, crs="EPSG:4326")
    return gdf

# Main function to retrieve and save traffic data
def save_traffic_data_as_geopackage(bbox, output_file):
    api_key = os.getenv("HERE_API_KEY")  # Access the API key from environment variables
    if not api_key:
        print("API key is not set.")
        return
    
    data = get_traffic_flow(bbox, api_key)
    if data:
        gdf = parse_traffic_data(data)
        gdf.to_file(output_file, driver="GPKG")
        print(f"Traffic data saved to {output_file}")
    else:
        print("Failed to get traffic data.")

# Set your bounding box (min_lng, min_lat, max_lng, max_lat) and output file path
bbox = "-47.237,-23.052,-46.948,-22.741"

# Generate a timestamped filename to avoid overwriting
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_file = f"traffic_data_{timestamp}.gpkg"

# Save the traffic data as a GeoPackage file
save_traffic_data_as_geopackage(bbox, output_file)
