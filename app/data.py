from dataclasses import dataclass
from pathlib import Path

import duckdb
from config import DUCKDB_CONFIG


@dataclass(frozen=True)
class DiaryEntry:
    id: int
    person_id: int
    text: str
    tags: list[str]


class DiaryDB:
    def __init__(self, db_location=str | Path) -> None:
        self.db_location = Path(db_location) if db_location != ":memory:" else db_location

        if isinstance(self.db_location, Path) and (not self.db_location.exists() or not self.db_location.is_file()):
            raise FileNotFoundError(f"File not found at {self.db_location}")

        self.conn = duckdb.connect(str(self.db_location), read_only=True, config=DUCKDB_CONFIG)

    def query_by_id(self, id: int) -> DiaryEntry:
        entry = self.conn.execute("SELECT id, person_id, text, tag FROM entries WHERE id = ?", [int(id)]).fetchone()

        if not entry:
            raise ValueError(f"Entry with ID {id} not found.")

        return DiaryEntry(*entry)

    def query_all_tags(self) -> list[str]:
        tags = self.conn.execute("SELECT DISTINCT unnest(tag) AS tag FROM entries ORDER BY tag;").fetchall()
        return [tag[0] for tag in tags]

    def query_similar(
        self,
        id: int,
        n: int = 5,
        tags: list | None = None,
        allow_same_person: bool = True,
    ) -> list[DiaryEntry]:
        """Find similar entries by ID.

        Args:
            con (duckdb.DuckDBPyConnection): Duckdb connection
            id (int): ID of the target entry
            n (int, optional): Number of relevant items to show. Defaults to 5.
            tags (list | None, optional): Tags to filter by. Defaults to None.
            allow_same_person (bool, optional): Wether to include entries by the same author as target's. Defaults to True.

        Returns:
            pd.DataFrame: Similar entries
        """
        if n < 1:
            ValueError("N must be greater than 0.")

        if tags and not isinstance(tags, list):
            ValueError("Tags must be a list, when provided.")

        query = """
            WITH t AS (
                SELECT id, person_id, vector FROM entries WHERE id = ?
            )

            SELECT
                e.id,
                e.person_id,
                e.text,
                e.tag

            FROM entries e JOIN t ON 1=1
            WHERE e.id != t.id AND e.tag @> ?
        """

        if not allow_same_person:
            query += " AND e.person_id != t.person_id"

        query += " ORDER BY array_cosine_similarity(t.vector, e.vector) DESC LIMIT ?;"

        entries = self.conn.execute(query, [int(id), tags or [], int(n)]).fetchall()

        return [DiaryEntry(*entry) for entry in entries]
