import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
import fiona

JOTR_VEG_GDB = "local_dev_data/input/jotrgeodata/jotrgeodata.gdb"
COMBINED_CSV = "local_dev_data/output/combined.csv"


def create_random_points():
    # Register the .gdb driver
    fiona.supported_drivers["FileGDB"] = "raw"

    # Read data
    layer_name = "JOTR_VegPolys"
    polygons = gpd.read_file(f"FileGDB:{JOTR_VEG_GDB}", layer=layer_name)

    # Read CSV with attributes
    attributes_df = pd.read_csv()

    # Merge polygons with attributes based on MapUnitID
    merged_data = polygons.merge(attributes_df, on="MapUnit_ID", how="left")

    # Initialize empty list for points
    points = []

    # Generate random points for each polygon
    for idx, row in merged_data.iterrows():
        polygon = row.geometry
        density = row.density  # Assuming 'density' is your density attribute

        # Calculate number of points based on area and density
        area = polygon.area
        num_points = int(area * density)

        # Generate random points within polygon bounds
        minx, miny, maxx, maxy = polygon.bounds

        points_count = 0
        while points_count < num_points:
            point = Point(np.random.uniform(minx, maxx), np.random.uniform(miny, maxy))
            if polygon.contains(point):
                points.append(
                    {
                        "geometry": point,
                        "properties": {
                            "MapUnitID": row.MapUnitID,
                            # Add other attributes as needed
                        },
                    }
                )
                points_count += 1

    # Create GeoDataFrame from points
    points_gdf = gpd.GeoDataFrame(
        points, geometry=[p["geometry"] for p in points], crs=polygons.crs
    )

    # Save to file
    points_gdf.to_file("random_points.gpkg", driver="GPKG")


if __name__ == "__main__":
    create_random_points()
