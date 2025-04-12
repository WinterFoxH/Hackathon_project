"""
Interactive Fire Risk Visualization for Podkarpacie
Loads data saved by Datacollection.py and creates an HTML map
with a fire risk overlay and high-risk alerts.
"""

import numpy as np
import folium
from folium.plugins import MarkerCluster, HeatMap # HeatMap potentially useful for other things
import branca.colormap as cm
from shared_data import load_fire_data # Updated function
from PIL import Image
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURATION ---
OUTPUT_HTML_FILE = 'podkarpacie_fire_risk_map.html'
TEMP_IMAGE_FILE = 'risk_overlay_temp.png' # Temporary file for the colored overlay
HIGH_RISK_THRESHOLD = 0.7 # Risk value (0-1) above which markers are placed
MAP_TILES = "CartoDB positron" # Cleaner background map
# MAP_TILES = "Stamen Terrain" # Alternative with terrain features
MAP_ZOOM_START = 11 # Adjust zoom level as needed
# --- END CONFIGURATION ---

def create_risk_map():
    # 1. Load processed data (including BBox)
    logging.info("Loading data from shared file...")
    loaded_data = load_fire_data()

    if loaded_data is None:
        logging.error("Failed to load data. Exiting.")
        return # Exit gracefully if data loading failed

    risk_data = loaded_data['risk']
    data_bbox = loaded_data['bbox'] # Use the BBox saved with the data

    # Ensure risk_data is 2D (height, width) and float 0-1
    if risk_data.ndim == 3:
         risk_data = risk_data.squeeze() # Remove singleton dimensions if any
    if risk_data.ndim != 2:
         logging.error(f"Unexpected risk data dimensions: {risk_data.ndim}. Expected 2D array.")
         return
    if risk_data.dtype != np.float32 and risk_data.dtype != np.float64:
        # Try converting if it's integer type (e.g., forgot normalization in collection)
        if np.issubdtype(risk_data.dtype, np.integer):
            logging.warning(f"Risk data type is {risk_data.dtype}. Assuming 0-255 range and normalizing to 0-1.")
            risk_data = risk_data.astype(np.float32) / 255.0
        else:
            logging.warning(f"Risk data type is {risk_data.dtype}. Attempting to convert to float32.")
            risk_data = risk_data.astype(np.float32)
    # Ensure values are roughly within 0-1 range
    if np.max(risk_data) > 1.1 or np.min(risk_data) < -0.1: # Allow slight margin
        logging.warning(f"Risk data range ({np.min(risk_data):.2f} - {np.max(risk_data):.2f}) seems outside 0-1. Clamping to 0-1 for visualization.")
        risk_data = np.clip(risk_data, 0.0, 1.0)


    logging.info(f"Risk data loaded, shape: {risk_data.shape}, dtype: {risk_data.dtype}, "
                 f"range: {np.min(risk_data):.2f}-{np.max(risk_data):.2f}")
    logging.info(f"Data Bounding Box: {data_bbox}")

    # 2. Set up map coordinates
    map_center = data_bbox.middle # Center map on the middle of the BBox
    logging.info(f"Map centered at: {map_center}")

    # 3. Create interactive map
    m = folium.Map(
        location=map_center,
        zoom_start=MAP_ZOOM_START,
        tiles=MAP_TILES,
        control_scale=True # Shows map scale
    )

    # 4. Prepare and add risk overlay
    # Create a colormap (Green=Low, Yellow=Medium, Red=High Risk)
    colormap = cm.LinearColormap(
        colors=['green', 'yellow', 'red'],
        vmin=0.0, vmax=1.0, # Risk data is expected to be normalized 0-1
        caption='Fire Risk Index (0=Low, 1=High)'
    )

    # Apply colormap to the risk data to get an RGBA image array
    # colormap function expects values between vmin and vmax
    colored_risk_rgba = colormap(risk_data, bytes=True) # Get RGBA values (0-255)

    # Create PIL Image from the RGBA array
    risk_img = Image.fromarray(colored_risk_rgba, 'RGBA')

    # Save the *colored* image temporarily
    try:
        risk_img.save(TEMP_IMAGE_FILE)
        logging.info(f"Saved temporary colored overlay to {TEMP_IMAGE_FILE}")
    except Exception as e:
        logging.error(f"Failed to save temporary image {TEMP_IMAGE_FILE}: {e}")
        return

    # Define overlay bounds from the data's BBox
    # Format for ImageOverlay bounds: [[min_lat, min_lon], [max_lat, max_lon]]
    overlay_bounds = [
        [data_bbox.min_y, data_bbox.min_x],
        [data_bbox.max_y, data_bbox.max_x]
    ]

    # Add the colored image as an overlay
    img_overlay = folium.raster_layers.ImageOverlay(
        image=TEMP_IMAGE_FILE, # Use the pre-colored temporary image
        bounds=overlay_bounds,
        opacity=0.6, # Adjust transparency
        name='Fire Risk Overlay',
        interactive=True,
        cross_origin=False,
        zindex=1,
    ).add_to(m)

    # Add the colormap legend to the map
    colormap.add_to(m)

    # 5. Add high-risk alerts
    logging.info(f"Adding markers for risk > {HIGH_RISK_THRESHOLD:.0%}")
    # Calculate latitudes and longitudes corresponding to pixel centers
    lats = np.linspace(data_bbox.max_y, data_bbox.min_y, risk_data.shape[0])
    lons = np.linspace(data_bbox.min_x, data_bbox.max_x, risk_data.shape[1])

    alerts_cluster = MarkerCluster(name=f"High Risk Alerts (> {HIGH_RISK_THRESHOLD:.0%})").add_to(m)
    alert_count = 0
    for i in range(risk_data.shape[0]): # Iterate over rows (latitude)
        for j in range(risk_data.shape[1]): # Iterate over columns (longitude)
            risk_value = risk_data[i, j]
            if risk_value > HIGH_RISK_THRESHOLD:
                alert_count += 1
                lat = lats[i]
                lon = lons[j]
                folium.Marker(
                    location=[lat, lon],
                    icon=folium.Icon(color='red', icon='fire', prefix='fa'), # Font Awesome fire icon
                    tooltip=f"Risk: {risk_value:.1%}", # Formatted percentage
                    popup=(f"High Fire Risk<br>"
                           f"Value: {risk_value:.3f}<br>"
                           f"Coords: {lat:.4f}N, {lon:.4f}E"),
                ).add_to(alerts_cluster)

    logging.info(f"Added {alert_count} high-risk alert markers.")
    if alert_count == 0:
         logging.info(f"No areas found with risk above the {HIGH_RISK_THRESHOLD:.0%} threshold.")

    # 6. Add controls and save
    folium.LayerControl().add_to(m) # Allows toggling layers (overlay, markers)
    m.save(OUTPUT_HTML_FILE)
    logging.info(f"✅ Interactive map saved to {OUTPUT_HTML_FILE}")

    # 7. Clean up temporary file
    try:
        os.remove(TEMP_IMAGE_FILE)
        logging.info(f"Removed temporary file {TEMP_IMAGE_FILE}")
    except OSError as e:
        logging.warning(f"Could not remove temporary file {TEMP_IMAGE_FILE}: {e}")

if __name__ == "__main__":
    create_risk_map()