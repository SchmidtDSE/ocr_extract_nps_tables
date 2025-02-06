import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
import fiona
from pyproj import Transformer
import random
import json

JOTR_VEG_GDB = "/workspaces/ocr_extract_nps_tables/local_dev_data/input/jotrgeodata/jotrgeodata.gdb"
COMBINED_CSV = "/workspaces/ocr_extract_nps_tables/local_dev_data/output/combined.csv"

AA_PLOT_SIZE_HECTARES = 0.5
JOTR_PER_HECTARE = 100
MIN_POINTS = 0

AGE_DIST_MU = 25
AGE_DIST_SIGMA = 30


def get_utm_zone(longitude):
    return int((longitude + 180) / 6) + 1


def transform_point_wgs84_utm(lon: float, lat: float, utm_zone: int = None) -> tuple:
    """Transform single point between WGS84 and UTM"""
    if utm_zone is None:
        utm_zone = int((lon + 180) / 6) + 1
    utm_crs = f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs"

    wgs84_to_utm = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)
    utm_to_wgs84 = Transformer.from_crs(utm_crs, "EPSG:4326", always_xy=True)

    return wgs84_to_utm, utm_to_wgs84


def create_random_points(species: str = None):
    # Register the .gdb driver
    fiona.supported_drivers["FileGDB"] = "raw"

    # Read data
    layer_name = "JOTR_VegPolys"
    polygons = gpd.read_file(JOTR_VEG_GDB, layer=layer_name)
    polygons = polygons.to_crs("EPSG:4326")
    polygons["MapUnit_ID"] = polygons["MapUnit_ID"].astype(np.int64)

    # Read CSV with attributes
    attributes_df = pd.read_csv(COMBINED_CSV)

    # Merge polygons with attributes
    merged_data = polygons.merge(attributes_df, on="MapUnit_ID", how="left")
    merged_data = merged_data[merged_data["Avg"].notnull()]
    merged_data = merged_data[merged_data["Species"] == species]
    points = []

    for idx, row in merged_data.iterrows():
        polygon = row.geometry
        cover_pct = row.Avg / 100.0

        if row.Avg == 0 or row.Avg is np.nan:
            continue

        # Get UTM zone for this polygon
        centroid = polygon.centroid
        utm_zone = get_utm_zone(centroid.x)
        utm_crs = f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs"

        # Convert polygon to UTM
        polygon_utm = gpd.GeoSeries([polygon], crs="EPSG:4326").to_crs(utm_crs)[0]

        # Calculate area in hectares (UTM coordinates are in meters)
        area_hectares = polygon_utm.area / 10000  # Convert m² to hectares

        # Calculate number of points (assuming a base density of determined above)
        num_trees_at_100_pct_cover = JOTR_PER_HECTARE * area_hectares
        num_points = max(MIN_POINTS, int(num_trees_at_100_pct_cover * cover_pct))

        # Set up transformers
        __wgs84_to_utm, utm_to_wgs84 = transform_point_wgs84_utm(
            centroid.x, centroid.y, utm_zone
        )

        # Generate points
        points_count = 0
        while points_count < num_points:
            minx, miny, maxx, maxy = polygon_utm.bounds
            point_utm = Point(
                np.random.uniform(minx, maxx), np.random.uniform(miny, maxy)
            )

            if polygon_utm.contains(point_utm):
                lon, lat = utm_to_wgs84.transform(point_utm.x, point_utm.y)

                # Random age
                age = int(max(0, round(np.random.normal(AGE_DIST_MU, AGE_DIST_SIGMA))))

                # Create point with random age
                points.append(
                    {
                        "type": "Feature",
                        "properties": {"age": age},
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    }
                )
                points_count += 1

        print(f"Created {len(points)} within polygon: {row.MapUnit_ID}")

    # Create the final GeoJSON structure
    geojson_output = {"type": "FeatureCollection", "features": points}

    return geojson_output


if __name__ == "__main__":
    points_geojson = create_random_points("Yucca brevifolia")
    with open("initial_JOTR_points.geojson", "w") as f:
        json.dump(points_geojson, f, indent=2)
