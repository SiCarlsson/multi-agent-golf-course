import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def convert_coordinates_to_points(
    coordinates: List[List[float]],
) -> List[Dict[str, float]]:
    """Convert GeoJSON coordinates [lon, lat] to frontend Point format {x, y}."""
    return [{"x": coord[0], "y": coord[1]} for coord in coordinates]


def extract_geometry_coordinates(geojson_data: Dict[str, Any]) -> List[List[float]]:
    """Extract coordinates from GeoJSON geometry, handling different geometry types."""
    features = geojson_data.get("features", [])
    all_coords = []

    for feature in features:
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])
        geom_type = geometry.get("type", "")

        if geom_type == "Polygon":
            if coords and len(coords) > 0:
                all_coords.extend(coords[0])  # Take outer ring
        elif geom_type == "MultiPolygon":
            for polygon in coords:
                if polygon and len(polygon) > 0:
                    all_coords.extend(polygon[0])  # Take outer ring of each polygon

    return all_coords


def extract_all_polygons(geojson_data: Dict[str, Any]) -> List[List[List[float]]]:
    """Extract all polygons separately from GeoJSON."""
    features = geojson_data.get("features", [])
    polygons = []

    for feature in features:
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])
        geom_type = geometry.get("type", "")

        if geom_type == "Polygon":
            if coords and len(coords) > 0:
                polygons.append(coords[0])  # Take outer ring
        elif geom_type == "MultiPolygon":
            for polygon in coords:
                if polygon and len(polygon) > 0:
                    polygons.append(polygon[0])  # Take outer ring of each polygon

    return polygons


def convert_hole_data(hole_number: int) -> Dict[str, Any]:
    """Convert raw GeoJSON files for a hole to frontend format."""
    raw_data_dir = Path(__file__).parent.parent / "data" / "geojson_raw"
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
        fairway_coords = extract_geometry_coordinates(fairway_geojson)
        hole_data["fairway"] = convert_coordinates_to_points(fairway_coords)

    # Process green
    green_path = hole_dir / "green.geojson"
    if green_path.exists():
        if green_path.stat().st_size == 0:
            raise ValueError(f"Empty file: {green_path}")
        with open(green_path, "r") as f:
            green_geojson = json.load(f)
        green_coords = extract_geometry_coordinates(green_geojson)
        hole_data["green"] = convert_coordinates_to_points(green_coords)

    # Process tees
    tees_path = hole_dir / "tees.geojson"
    if tees_path.exists():
        if tees_path.stat().st_size == 0:
            raise ValueError(f"Empty file: {tees_path}")
        with open(tees_path, "r") as f:
            tees_geojson = json.load(f)
        tees_polygons = extract_all_polygons(tees_geojson)
        hole_data["tees"] = [
            convert_coordinates_to_points(tee) for tee in tees_polygons
        ]

    # Process bunkers
    bunkers_path = hole_dir / "bunkers.geojson"
    if bunkers_path.exists():
        if bunkers_path.stat().st_size == 0:
            raise ValueError(f"Empty file: {bunkers_path}")
        with open(bunkers_path, "r") as f:
            bunkers_geojson = json.load(f)
        bunkers_polygons = extract_all_polygons(bunkers_geojson)
        hole_data["bunkers"] = [
            convert_coordinates_to_points(bunker) for bunker in bunkers_polygons
        ]

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
        json.dump(hole_data, f, indent=2)

    return hole_data


def convert_all_holes() -> None:
    """Convert all available holes from raw GeoJSON to frontend format."""
    raw_data_dir = Path(__file__).parent.parent / "data" / "geojson_raw"

    hole_dirs = sorted(
        [d for d in raw_data_dir.iterdir() if d.is_dir() and d.name.startswith("hole_")]
    )

    converted_count = 0
    for hole_dir in hole_dirs:
        hole_number = int(hole_dir.name.split("_")[1])
        convert_hole_data(hole_number)
        converted_count += 1
        logger.info(f"Converted hole {hole_number}")

    logger.info(f"Successfully converted {converted_count} holes")


if __name__ == "__main__":
    convert_all_holes()
