from dataclasses import asdict
import random

import streamlit as st

from .components import diary_card, diary_snippets
from .config import DB_LOCATION, STARTING_ENTRIES
from .data import DiaryDB, DiaryEntry

# --- Resource loading ---

@st.cache_resource(max_entries=1, show_spinner="Загрузка базы данных...")
def get_db() -> DiaryDB:
    return DiaryDB(DB_LOCATION)


@st.cache_data(max_entries=1, show_spinner="Загрузка тегов...")
def get_all_tags() -> list[str]:
    return get_db().query_all_tags()


@st.cache_data(max_entries=1, hash_funcs={DiaryEntry: asdict}, show_spinner="Загрузка записи...")
def get_entry(entry_id: DiaryEntry, /) -> dict:
    return get_db().query_by_id(entry_id)


@st.cache_data(max_entries=1, hash_funcs={DiaryEntry: asdict}, show_spinner="Загрузка похожих записей...")
def get_similar(entry_id: DiaryEntry, /, tags: list[str], n: int = 3, allow_same_person: bool = True) -> list[dict]:
    return get_db().query_similar(entry_id, tags=tags, n=n, allow_same_person=allow_same_person)


# --- Main app logic ---


def add_tag(tag: str | None):
    if "tag_filter" in st.session_state and tag not in st.session_state.tag_filter:
        st.session_state.tag_filter.append(tag)
    elif "tag_filter" not in st.session_state:
        st.session_state.tag_filter = [tag]


def update_tag_filter(tags: list[str]):
    st.session_state.tag_filter = tags
    get_similar.clear()


def change_entry(entry: DiaryEntry):
    st.session_state.current_entry_id = entry.id
    get_entry.clear()
    get_similar.clear()


def main() -> None:
    # --- Session state initialization ---

    TAGS = get_all_tags()

    if "current_entry_id" not in st.session_state:
        st.session_state.current_entry_id = random.choice(STARTING_ENTRIES)

    if "current_author_id" not in st.session_state:
        st.session_state.current_author_id = -1

    if "tag_filter" not in st.session_state:
        st.session_state.tag_filter = []

    # --- App Layout ---
    current_entry = get_entry(st.session_state.current_entry_id)
    st.session_state.current_author_id = current_entry.person_id

    diary_card(current_entry, tag_callback=add_tag)

    st.header("Похожие записи", divider=True)

    selected_tags = st.multiselect(
        "Фильтровать похожие записи по тегам", options=TAGS, default=st.session_state.tag_filter
    )

    allow_same_person = st.toggle("Отображать записи от того же автора", value=True)

    if selected_tags != st.session_state.tag_filter:
        st.session_state.tag_filter = selected_tags
        get_similar.clear()
        st.rerun()

    # Display snippets of related entries
    similar_entries = get_similar(
        st.session_state.current_entry_id,
        tags=st.session_state.tag_filter,
        n=5,
        allow_same_person=allow_same_person,
    )
    diary_snippets(similar_entries, entry_callback=change_entry)


if __name__ == "__main__":
    main()
