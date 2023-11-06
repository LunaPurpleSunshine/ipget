import datetime
import logging
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
    name_path = Path(name).resolve()
    stem = str(name_path.stem).replace(".log", "")
    if not all([stem, name_path.suffix]):
        raise ValueError(name)
    log_dir = name_path.parent
    date = str(datetime.datetime.now().date())
    # return str(log_dir.joinpath(f"ipget.{date}.log"))
    return str(log_dir.joinpath(f"{stem}.{date}.log"))
