import logging
from backend.scripts.convert_geojson import convert_all_holes

logger = logging.getLogger(__name__)


def regenerate_course_data() -> None:
    """Regenerate all course data files from raw GeoJSON."""
    logger.info("Regenerating course data from raw GeoJSON files...")
    convert_all_holes()
    logger.info("Course data regeneration complete")
