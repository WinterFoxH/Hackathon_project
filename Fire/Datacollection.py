"""
Optimized Data Collector for PODKARPACIE_FIRE_RISK Layer
Downloads Sentinel-2 L2A data for a specified layer and area,
saves false color, NDVI, risk, and bounding box using shared_data.
"""

from sentinelhub import (
    WmsRequest, BBox, CRS, MimeType, # Correct import for MimeType
    SHConfig, DataCollection, SentinelHubRequest, # Added SentinelHubRequest if needed later
    SentinelHubDownloadClient # Added for potential alternative downloads
)
import numpy as np
from shared_data import save_fire_data
import sys
from datetime import datetime
import logging # Use logging for better message handling

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURATION ---
# BBox for the Bieszczady Mountains region (adjust as needed)
# Format: [min_longitude, min_latitude, max_longitude, max_latitude]
TARGET_BBOX_COORDS = [22.0, 49.2, 22.5, 49.5]
TARGET_CRS = CRS.WGS84

# Sentinel Hub Layer Name (must match your configuration in Sentinel Hub Dashboard)
SH_LAYER_NAME = 'PODKARPACIE_FIRE_RISK'

# Image resolution (width and height in pixels)
IMG_WIDTH = 512 # Increased resolution
IMG_HEIGHT = 512

# Maximum acceptable cloud cover (0.0 to 1.0)
MAX_CLOUD_COVER = 0.20

# Dates to attempt download (most recent first is often desired)
# Add more known good dates or specific dates of interest
DATES_TO_TRY = [
    'latest',       # Try most recent available first
    '2023-08-15',   # Historically clear date
    '2023-08-02',
    '2023-07-28',
    # Add more dates if needed
]
# --- END CONFIGURATION ---


def download_data_for_date(config, layer, bbox, time_str, width, height, maxcc):
    """Attempts to download data for a specific date."""
    logging.info(f"Attempting download for time='{time_str}', layer='{layer}'...")
    try:
        request = WmsRequest(
            data_collection=DataCollection.SENTINEL2_L2A,
            layer=layer,
            bbox=bbox,
            time=time_str,
            width=width,
            height=height,
            image_format=MimeType.PNG, # Correct MimeType usage (faster than TIFF)
            # Using PNG assumes your layer outputs 8-bit data correctly scaled 0-255
            # If your layer outputs raw data (e.g. float NDVI), TIFF (MimeType.TIFF) might be better
            config=config,
            maxcc=maxcc,
            # time_difference=datetime.timedelta(hours=2), # Optional: tolerance for 'latest'
        )

        data = request.get_data() # Returns a list of numpy arrays

        # Verify structure: Expecting 3 arrays (bands/outputs from the layer)
        if not isinstance(data, list) or len(data) != 3:
            raise ValueError(f"Expected 3 image arrays (bands/outputs) from layer '{layer}', but received {len(data)}.")

        # Optional: Check array shapes (can be useful for debugging)
        # expected_shape = (height, width, 3) # For RGB-like false color
        # if data[0].shape != expected_shape:
        #     logging.warning(f"Unexpected shape for false_color: {data[0].shape}, expected {expected_shape}")
        # expected_shape_single = (height, width) # For single band like NDVI/Risk if output as grayscale
        # if data[1].ndim != 2 or data[1].shape != expected_shape_single:
        #      logging.warning(f"Unexpected shape for ndvi: {data[1].shape}, expected {expected_shape_single}")
        # if data[2].ndim != 2 or data[2].shape != expected_shape_single:
        #      logging.warning(f"Unexpected shape for risk: {data[2].shape}, expected {expected_shape_single}")

        logging.info(f"Successfully downloaded data for time='{time_str}'.")
        return data

    except Exception as e:
        logging.warning(f"Download attempt failed for time='{time_str}': {e}")
        return None


def main():
    # 1. Load Sentinel Hub configuration
    try:
        config = SHConfig()
        if not config.sh_client_id or not config.sh_client_secret:
            logging.error("Sentinel Hub credentials (SH_CLIENT_ID, SH_CLIENT_SECRET) not found.")
            logging.error("Please configure them via environment variables or a config file.")
            sys.exit(1)
        logging.info("Sentinel Hub configuration loaded.")
    except Exception as e:
        logging.error(f"Failed to load SHConfig: {e}")
        sys.exit(1)

    # 2. Define area of interest
    target_bbox = BBox(TARGET_BBOX_COORDS, crs=TARGET_CRS)
    logging.info(f"Target BBox: {target_bbox}")

    # 3. Iterate through dates and attempt download
    downloaded_data = None
    successful_date = None

    for date_str in DATES_TO_TRY:
        data = download_data_for_date(
            config=config,
            layer=SH_LAYER_NAME,
            bbox=target_bbox,
            time_str=date_str,
            width=IMG_WIDTH,
            height=IMG_HEIGHT,
            maxcc=MAX_CLOUD_COVER
        )

        if data:
            downloaded_data = data
            successful_date = date_str
            break # Stop after first successful download

    # 4. Process results
    if downloaded_data:
        logging.info(f"✅ Success! Data obtained for date: {successful_date}")

        # Assume order from layer: [False Color, NDVI, Risk]
        # Adapt if your layer 'PODKARPACIE_FIRE_RISK' outputs in a different order
        false_color_img = downloaded_data[0]
        ndvi_img = downloaded_data[1]
        risk_img = downloaded_data[2]

        # Assuming WMS returns uint8 PNG:
        # - false_color_img shape might be (h, w, 3) or (h, w, 4) if alpha included
        # - ndvi_img and risk_img shape might be (h, w) if single band grayscale

        # Make sure risk is single band (e.g., grayscale)
        if risk_img.ndim == 3 and risk_img.shape[2] > 1:
             logging.warning(f"Risk image has multiple channels (shape {risk_img.shape}). Using the first channel.")
             risk_img = risk_img[..., 0]
        elif risk_img.ndim == 3 and risk_img.shape[2] == 1:
             risk_img = risk_img.squeeze(axis=2) # Remove last dimension if it's 1

        # Normalize risk to 0-1 if it's currently 0-255 (uint8)
        # Check data type. If it's float, it might already be 0-1.
        if risk_img.dtype == np.uint8:
             logging.info("Risk map appears to be uint8 (0-255), normalizing to float (0-1).")
             risk_img = risk_img.astype(np.float32) / 255.0
        elif np.max(risk_img) > 1.0 or np.min(risk_img) < 0.0:
             # Add normalization if needed for other data types/ranges
             logging.warning(f"Risk map data range ({np.min(risk_img):.2f} - {np.max(risk_img):.2f}) seems outside 0-1. Check layer configuration.")
             # Example: Clamp values if necessary
             # risk_img = np.clip(risk_img, 0.0, 1.0)


        # Save the data using the shared function
        save_fire_data(
            false_color=false_color_img,
            ndvi=ndvi_img,
            risk=risk_img, # Save the potentially normalized risk map
            bbox=target_bbox # Save the BBox used for the download
        )
        sys.exit(0) # Exit successfully

    else:
        logging.error("❌ All download attempts failed.")
        logging.error("Please verify:")
        logging.error(f"1. Your Sentinel Hub layer '{SH_LAYER_NAME}' exists and is configured correctly.")
        logging.error("   - Test it in EO Browser or Sentinel Hub Dashboard Request Builder.")
        logging.error("   - Ensure it outputs exactly 3 results (e.g., False Color, NDVI, Risk).")
        logging.error(f"2. Data availability for the target BBox {target_bbox} and dates: {DATES_TO_TRY}.")
        logging.error(f"3. Cloud cover ({MAX_CLOUD_COVER*100}%) was not too high for available dates.")
        logging.error("4. Your Sentinel Hub instance is active and has sufficient processing units.")
        sys.exit(1)


if __name__ == "__main__":
    main()