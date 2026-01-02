import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from pyproj import Transformer

logger = logging.getLogger(__name__)

# Create transformer from WGS84 (lat/lon) to UTM Zone 33N (Sweden)
# EPSG:4326 = WGS84 (latitude/longitude)
# EPSG:32633 = WGS84 / UTM zone 33N
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)


def convert_lonlat_to_utm(lon: float, lat: float) -> tuple[float, float]:
    """Convert longitude/latitude to UTM x/y in meters."""
    return transformer.transform(lon, lat)


def convert_coordinates_to_points(
    coordinates: List[List[float]], origin_utm: Optional[tuple[float, float]] = None
) -> tuple[List[Dict[str, float]], Optional[tuple[float, float]]]:
    """Convert GeoJSON coordinates [lon, lat] to frontend Point format {x, y} in meters.

    Returns:
        tuple: (converted points, origin_utm used for conversion)
    """
    if origin_utm is None and coordinates:
        origin_utm = convert_lonlat_to_utm(coordinates[0][0], coordinates[0][1])

    points = []
    for coord in coordinates:
        x_utm, y_utm = convert_lonlat_to_utm(coord[0], coord[1])
        # Convert to relative coordinates (meters from origin)
        points.append({"x": x_utm - origin_utm[0], "y": y_utm - origin_utm[1]})

    return points, origin_utm


def extract_polygons(
    geojson_data: Dict[str, Any], flatten: bool = False
) -> List[List[float]] | List[List[List[float]]]:
    """Extract polygon coordinates from GeoJSON geometry."""
    features = geojson_data.get("features", [])
    polygons = []

    for feature in features:
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])
        geom_type = geometry.get("type", "")

        if geom_type == "Polygon":
            polygons.append(coords[0])
        elif geom_type == "MultiPolygon":
            for polygon in coords:
                polygons.append(polygon[0])

    if flatten:
        coords = []
        for polygon in polygons:
            for coord in polygon:
                coords.append(coord)
        return coords

    return polygons


def convert_hole_data(
    hole_number: int, origin_utm: Optional[tuple[float, float]] = None
) -> tuple[Dict[str, Any], Optional[tuple[float, float]]]:
    """Convert raw GeoJSON files for a hole to frontend format.

    Args:
        hole_number: The hole number to convert
        origin_utm: Optional UTM origin to maintain spatial relationships between holes

    Returns:
        tuple: (hole data dict, origin_utm used for conversion)
    """
    raw_data_dir = Path(__file__).parent.parent / "data" / "geojson"
    hole_dir = raw_data_dir / f"hole_{hole_number:02d}"

    if not hole_dir.exists():
        raise ValueError(f"Hole directory not found: {hole_dir}")

    hole_data = {}

    # Process fairway
    fairway_path = hole_dir / "fairway.geojson"
    if fairway_path.exists():
        if fairway_path.stat().st_size == 0:
            raise ValueError(f"Empty file: {fairway_path}")
        with open(fairway_path, "r") as f:
            fairway_geojson = json.load(f)
        fairway_coords = extract_polygons(fairway_geojson, flatten=True)
        hole_data["fairway"], origin_utm = convert_coordinates_to_points(
            fairway_coords, origin_utm
        )

    # Process green
    green_path = hole_dir / "green.geojson"
    if green_path.exists():
        if green_path.stat().st_size == 0:
            raise ValueError(f"Empty file: {green_path}")
        with open(green_path, "r") as f:
            green_geojson = json.load(f)
        green_coords = extract_polygons(green_geojson, flatten=True)
        hole_data["green"], origin_utm = convert_coordinates_to_points(
            green_coords, origin_utm
        )

    # Process tees
    tees_path = hole_dir / "tees.geojson"
    if tees_path.exists():
        if tees_path.stat().st_size == 0:
            raise ValueError(f"Empty file: {tees_path}")
        with open(tees_path, "r") as f:
            tees_geojson = json.load(f)
        tees_polygons = extract_polygons(tees_geojson)
        tees_data = []
        for tee in tees_polygons:
            tee_points, origin_utm = convert_coordinates_to_points(tee, origin_utm)
            tees_data.append(tee_points)
        hole_data["tees"] = tees_data

    # Process bunkers
    bunkers_path = hole_dir / "bunkers.geojson"
    if bunkers_path.exists():
        if bunkers_path.stat().st_size == 0:
            raise ValueError(f"Empty file: {bunkers_path}")
        with open(bunkers_path, "r") as f:
            bunkers_geojson = json.load(f)
        bunkers_polygons = extract_polygons(bunkers_geojson)
        bunkers_data = []
        for bunker in bunkers_polygons:
            bunker_points, origin_utm = convert_coordinates_to_points(
                bunker, origin_utm
            )
            bunkers_data.append(bunker_points)
        hole_data["bunkers"] = bunkers_data

    # Initial flag position set to the center of green as default
    # Note: Flag position will be managed by the green-keeper agent at runtime
    if "green" in hole_data and hole_data["green"]:
        green_points = hole_data["green"]
        avg_x = sum(p["x"] for p in green_points) / len(green_points)
        avg_y = sum(p["y"] for p in green_points) / len(green_points)
        hole_data["flag"] = {"x": avg_x, "y": avg_y}

    output_dir = Path(__file__).parent.parent / "data" / "course"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"hole_{hole_number:02d}.json"

    with open(output_file, "w") as f:
        json.dump(hole_data, f, indent=4)

    return hole_data, origin_utm


def convert_all_holes() -> None:
    """Convert all available holes from raw GeoJSON to frontend format."""
    raw_data_dir = Path(__file__).parent.parent / "data" / "geojson"

    hole_dirs = sorted(
        [d for d in raw_data_dir.iterdir() if d.is_dir() and d.name.startswith("hole_")]
    )

    origin_utm = None
    converted_count = 0
    for hole_dir in hole_dirs:
        hole_number = int(hole_dir.name.split("_")[1])
        _, origin_utm = convert_hole_data(hole_number, origin_utm)
        converted_count += 1
        logger.info(f"Converted hole {hole_number}")

    logger.info(f"Successfully converted {converted_count} holes")
