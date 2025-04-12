from sentinelhub import WmsRequest, MimeType, CRS, BBox

# Podkarpacie bounding box [minx, miny, maxx, maxy]
podkarpacie_bbox = [21.0, 49.0, 23.5, 50.5]

# Get NDVI (vegetation health)
ndvi_request = WmsRequest(
    layer='NDVI',
    bbox=podkarpacie_bbox,
    time=('2023-06-01', '2023-09-30'),  # Fire season
    width=1024,
    image_format=MimeType.TIFF
)

# Get thermal data for hotspots
thermal_request = WmsRequest(
    layer='THERMAL',
    bbox=podkarpacie_bbox,
    time=('2023-06-01', '2023-09-30'),
    width=1024,
    image_format=MimeType.TIFF
)