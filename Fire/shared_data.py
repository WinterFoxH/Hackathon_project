"""
Data bridge between collection and processing modules
Handles saving/loading of numpy arrays and associated metadata (like BBox).
"""

import numpy as np
import os
from sentinelhub import BBox, CRS # Added for BBox type hinting if needed

# File paths
DATA_FILE = "fire_data.npz"
BACKUP_FILE = "fire_data_backup.npz"

def save_fire_data(false_color, ndvi, risk, bbox):
    """
    Save satellite data and its bounding box to a compressed numpy file.

    Args:
        false_color (np.ndarray): False color image array (e.g., RGB).
        ndvi (np.ndarray): NDVI data array.
        risk (np.ndarray): Fire risk data array.
        bbox (sentinelhub.BBox): Bounding box of the downloaded data.
    """
    try:
        # Create backup if file exists
        if os.path.exists(DATA_FILE):
            print(f"Backing up existing {DATA_FILE} to {BACKUP_FILE}")
            os.replace(DATA_FILE, BACKUP_FILE)

        # Convert BBox to a savable list [min_x, min_y, max_x, max_y]
        # and save CRS identifier (e.g., 'CRS.WGS84')
        bbox_coords = list(bbox.geometry.bounds)
        bbox_crs_epsg = bbox.crs.epsg # Store EPSG code

        np.savez(DATA_FILE,
                 false_color=false_color,
                 ndvi=ndvi,
                 risk=risk,
                 bbox_coords=np.array(bbox_coords), # Save coords as numpy array
                 bbox_crs_epsg=bbox_crs_epsg)       # Save EPSG code

        print(f"Data and BBox saved to {DATA_FILE}")

    except Exception as e:
        print(f"Failed to save data: {str(e)}")
        # Attempt to restore from backup if save failed
        if os.path.exists(BACKUP_FILE):
            try:
                os.replace(BACKUP_FILE, DATA_FILE)
                print("Restored previous data version from backup.")
            except Exception as restore_e:
                print(f"Failed to restore backup: {restore_e}")
        # Make sure backup doesn't linger if original file didn't exist
        elif os.path.exists(DATA_FILE):
             os.remove(DATA_FILE) # Clean up failed save attempt
    finally:
        # Clean up backup file if save was successful
        if os.path.exists(BACKUP_FILE) and os.path.exists(DATA_FILE):
             # Check if DATA_FILE was successfully created *after* backup
             # A more robust check might involve comparing modification times or content
             try:
                 os.remove(BACKUP_FILE)
                 print(f"Removed backup file {BACKUP_FILE}")
             except Exception as remove_e:
                 print(f"Could not remove backup file {BACKUP_FILE}: {remove_e}")


def load_fire_data():
    """
    Load saved satellite data and its bounding box.

    Returns:
        dict: Dictionary containing 'false_color', 'ndvi', 'risk' arrays
              and 'bbox' (sentinelhub.BBox object).
              Returns None if loading fails.
    """
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found. Run Datacollection.py first!")
        return None # Return None instead of exiting

    try:
        with np.load(DATA_FILE) as data:
            # Reconstruct BBox object
            bbox_coords = data['bbox_coords'].tolist()
            bbox_crs = CRS(epsg=int(data['bbox_crs_epsg'])) # Recreate CRS from EPSG
            bbox = BBox(bbox_coords, crs=bbox_crs)

            return {
                'false_color': data['false_color'],
                'ndvi': data['ndvi'],
                'risk': data['risk'],
                'bbox': bbox # Include the reconstructed BBox object
            }
    except KeyError as e:
        print(f"Error loading data: Missing key {e} in {DATA_FILE}. "
              "The file might be corrupted or from an older version.")
        return None
    except Exception as e:
        print(f"Error loading data from {DATA_FILE}: {str(e)}")
        return None