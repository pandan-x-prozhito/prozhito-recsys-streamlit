import random
import uuid

import streamlit as st

from .components import diary_card, diary_snippets, local_css
from .config import DB_LOCATION, DB_ZIP_PASSWORD, STARTING_ENTRIES
from .data import DiaryDB, DiaryEntry
from .exceptions import DataError, EntryNotFound
from .log import logger

# --- Resource loading ---


@st.cache_resource(max_entries=1, show_spinner="Загрузка базы данных...")
def get_db() -> DiaryDB:
    return DiaryDB(DB_LOCATION, zip_password=DB_ZIP_PASSWORD)


@st.cache_resource(max_entries=10, show_spinner="Загрузка тегов...")
def get_all_tags() -> list[str]:
    return get_db().query_all_tags()


@st.cache_resource(max_entries=10, show_spinner="Загрузка записи...")
def get_entry(entry_id: DiaryEntry, /) -> dict:
    logger.info(f"Loading entry: {entry_id}")
    return get_db().query_by_id(entry_id)


@st.cache_resource(max_entries=10, show_spinner="Загрузка похожих записей...")
def get_similar(entry_id: DiaryEntry, /, tags: list[str], n: int = 3, allow_same_person: bool = True) -> list[dict]:
    logger.debug(f"Loading similar entries for: {entry_id}")
    return get_db().query_similar(entry_id, tags=tags, n=n, allow_same_person=allow_same_person)


# --- Main app logic ---


def add_tag(tag: str | None):
    if "tag_filter" in st.session_state and tag not in st.session_state.tag_filter:
        st.session_state.tag_filter.append(tag)
    elif "tag_filter" not in st.session_state:
        st.session_state.tag_filter = [tag]


def update_tag_filter(tags: list[str]):
    st.session_state.tag_filter = tags


def change_entry(entry: DiaryEntry):
    st.session_state.current_entry_id = entry.id


def main() -> None:
    local_css("static/styles.css")
    # --- Session state initialization ---

    try:
        TAGS = get_all_tags()
    except (EntryNotFound, DataError) as e:
        logger.exception(e)
        st.error("Не удалось получить теги. Попробуйте перезагрузить страницу.")
        st.stop()
    if "session_uuid" not in st.session_state:
        st.session_state.session_uuid = uuid.uuid4()
        logger.info(f"Starting session: {st.session_state.session_uuid.hex[:10]}")

    if "current_entry_id" not in st.session_state:
        st.session_state.current_entry_id = random.choice(STARTING_ENTRIES)
        logger.info(f"Starting with entry: {st.session_state.current_entry_id}")

    if "current_author_id" not in st.session_state:
        st.session_state.current_author_id = -1

    if "tag_filter" not in st.session_state:
        st.session_state.tag_filter = []

    # --- App Layout ---
    try:
        current_entry = get_entry(st.session_state.current_entry_id)
        st.session_state.current_author_id = current_entry.person_id
    except (EntryNotFound, DataError) as e:
        logger.exception(e)
        st.error("Не удалось получить запись. Попробуйте перезагрузить страницу")
        st.stop()

    diary_card(current_entry, tag_callback=add_tag)

    st.header("Похожие записи", divider=True)

    selected_tags = st.multiselect(
        "Фильтровать похожие записи по тегам", options=TAGS, default=st.session_state.tag_filter
    )

    allow_same_person = st.toggle("Отображать записи от того же автора", value=True)

    if selected_tags != st.session_state.tag_filter:
        st.session_state.tag_filter = selected_tags
        st.rerun()

    # Display snippets of related entries
    try:
        similar_entries = get_similar(
            st.session_state.current_entry_id,
            tags=st.session_state.tag_filter,
            n=5,
            allow_same_person=allow_same_person,
        )
    except (EntryNotFound, DataError) as e:
        logger.exception(e)
        st.error("Не удалось получить похожие записи. Попробуйте перезагрузить страницу.")
        st.stop()

    diary_snippets(similar_entries, entry_callback=change_entry)


if __name__ == "__main__":
    main()
