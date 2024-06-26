from dataclasses import dataclass
from pathlib import Path

import duckdb
import pyzipper

from .config import DUCKDB_CONFIG
from .exceptions import DataError, EntryNotFound
from .log import logger


@dataclass(frozen=True)
class DiaryEntry:
    """
    Represents a diary entry.

    Attributes:
        id (int): The unique identifier of the diary entry.
        person_id (int): The identifier of the person who wrote the diary entry.
        text (str): The text content of the diary entry.
        tags (list[str]): The list of tags associated with the diary entry.
    """
    id: int
    person_id: int
    text: str
    tags: list[str]


class DiaryDB:
    def __init__(self, db_location: str | Path, zip_password: str | None = None) -> None:
        """
        Initializes the Data class.

        Args:
            db_location (str | Path): The location of the database file or ":memory:" for an in-memory database.
            zip_password (str | None, optional): The password for the zip file, if the database is stored in a zip file. Defaults to None.

        Raises:
            FileNotFoundError: If the database file is not found at the specified location.
        """
        self.db_location = Path(db_location) if db_location != ":memory:" else db_location

        if isinstance(self.db_location, Path) and (not self.db_location.exists() or not self.db_location.is_file()):
            raise FileNotFoundError(f"File not found at {self.db_location}")

        if self.db_location.suffix == ".zip":
            self.__unzip(zip_password)

        self.conn = duckdb.connect(str(self.db_location), read_only=True, config=DUCKDB_CONFIG)
        logger.info(f"Connected to database at {self.db_location}")

    def __unzip(self, password: str | None) -> None:
        if not pyzipper.is_zipfile(self.db_location):
            raise ValueError("File is not a zip archive.")

        with pyzipper.AESZipFile(self.db_location, "r") as zip_ref:
            fname = zip_ref.namelist()[0]
            new_location = self.db_location.parent / fname
            if not (new_location.exists() and new_location.is_file()):
                zip_ref.extract(fname, self.db_location.parent, pwd=password.encode() if password else None)
                logger.info(f"Extracted {fname} from {self.db_location}")

        self.db_location = new_location

    def __del__(self) -> None:
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
            logger.info("Disconnected from database.")

    def __reinit(self):
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
        self.conn = duckdb.connect(str(self.db_location), read_only=True, config=DUCKDB_CONFIG)
        logger.info(f"Reconnected to database at {self.db_location}")

    def query_by_id(self, id: int) -> DiaryEntry:
        """Query a diary entry by its ID.

        Args:
            id (int): The ID of the diary entry to query.

        Raises:
            DataError: If an error occurs while querying the database.
            EntryNotFound: If the entry with the specified ID is not found.

        Returns:
            DiaryEntry: The queried diary entry.

        """
        try:
            entry = self.conn.execute("SELECT id, person_id, text, tag FROM entries WHERE id = ?", [int(id)]).fetchone()
        except duckdb.InternalException as e:
            self.__reinit()
            raise DataError(f"An error occurred while querying the database: {e}") from e

        if not entry:
            raise EntryNotFound(f"Entry with ID {id} not found.")

        return DiaryEntry(*entry)

    def query_all_tags(self) -> list[str]:
        """Get all tags from the database.

        This method queries the database to retrieve all distinct tags from the 'entries' table.
        The tags are returned as a list of strings.

        Raises:
            DataError: If an error occurs while querying the database.
            EntryNotFound: If no tags are found in the database.

        Returns:
            list[str]: A list of all tags from the database.
        """
        try:
            tags = self.conn.execute("SELECT DISTINCT unnest(tag) AS tag FROM entries ORDER BY tag;").fetchall()
        except duckdb.InternalException as e:
            self.__reinit()
            raise DataError(f"An error occurred while querying the database: {e}") from e

        if not tags:
            raise EntryNotFound("No tags found in the database.")

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

        Raises:
            DataError: If an error occurs while querying the database.
            EntryNotFound: If no similar entries are found.

        Returns:
            list[DiaryEntry]: Similar entries
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

        try:
            entries = self.conn.execute(query, [int(id), tags or [], int(n)]).fetchall()
        except duckdb.InternalException as e:
            self.__reinit()
            raise DataError(f"An error occurred while querying the database: {e}") from e

        if not entries:
            raise EntryNotFound(f"No similar entries found for ID {id}.")

        return [DiaryEntry(*entry) for entry in entries]
