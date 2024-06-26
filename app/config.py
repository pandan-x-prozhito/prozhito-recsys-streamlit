import os
from typing import Any

DB_LOCATION: str = "data/diaries_vec.db.zip"
DB_ZIP_PASSWORD: str | None = os.getenv("DB_ZIP_PASSWORD", None)
STARTING_ENTRIES: list[int] = [
    94325,
    180144,
    223688,
    239369,
    316742,
    336627,
    380619,
    463102,
    515346,
    565701,
    597109,
    646277,
    697019,
    703364,
    706409,
    719845,
    725211,
    739503,
    764570,
    786819,
]
DUCKDB_CONFIG: dict[str, Any] = {"memory_limit": "384MB", "threads": 1}
