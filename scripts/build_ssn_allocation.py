import json
import logging
import pickle
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "tax_identifiers" / "us" / "static"
JSON_FILE = STATIC_DIR / "ssn_allocation.json"
PICKLE_FILE = STATIC_DIR / "ssn_allocation.pkl"


def main() -> None:
    """Build the pickled SSN allocation dataset from the JSON source of truth."""

    with JSON_FILE.open(encoding="utf-8") as source_file:
        data = json.load(source_file)

    with PICKLE_FILE.open("wb") as target_file:
        pickle.dump(data, target_file, protocol=pickle.HIGHEST_PROTOCOL)

    logger.info("Wrote %d SSN allocation entries to %s", len(data), PICKLE_FILE)


if __name__ == "__main__":
    main()
