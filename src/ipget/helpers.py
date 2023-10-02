import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)


def custom_namer(name: str) -> str:
    """Custom namer for a RotatingFileHandler.
    Inserts the date between the stem and the final suffix.

    Args:
        name (str): The name of the file.

    Returns:
        str: The custom name generated for the file.

    Example:
        `ipget.log` → `ipget.2023-10-02.log`
    """
    if not isinstance(name, str):
        raise TypeError(name)
    name_path = Path(name)
    stem = name_path.stem
    if not all([name, stem, name_path.suffix]):
        raise ValueError(name)
    date = str(datetime.now().date())
    return f"{stem}.{date}{name_path.suffix}"
