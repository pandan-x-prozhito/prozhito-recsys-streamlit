import re

import streamlit as st

from data import DiaryEntry

BR_RE = re.compile(r"<br\s*?/?>")
TAG_RE = re.compile(r"<[^>]+>")
SPACES_RE = re.compile(r"\s+")


def clean_entry_text(text):
    text = BR_RE.sub("\n", text)
    text = TAG_RE.sub("", text)
    text = SPACES_RE.sub(" ", text)
    return text


def diary_card(entry: DiaryEntry, /, tag_callback: callable) -> None:
    st.header("Дневниковая запись")

    with st.container(border=True, height=300):
        st.markdown(entry.text, unsafe_allow_html=True)

    st.subheader("Теги", divider=True)
    tag_cols = st.columns(len(entry.tags))

    for tag, col in zip(entry.tags, tag_cols):
        with col:
            st.button(
                tag,
                key=f"tag_button_{tag}",
                on_click=lambda t=tag: tag_callback(t),
                help=f'Добавить тег "{tag}" в фильтр',
            )


def diary_snippets(entries: list[DiaryEntry], /, entry_callback: callable) -> None:
    if not entries:
        st.warning("Похожих записей не найдено.")
        return
    for entry in entries:
        with st.container(border=True):
            col_text, col_button = st.columns([0.75, 0.25])

        text: str = clean_entry_text(entry.text)
        text = text[:80] + "..." if len(text) > 80 else text

        if "current_author_id" in st.session_state and st.session_state.current_author_id == entry.person_id:
            text += "\n*– Тот же автор*"

        with col_text:
            st.markdown(text)

        with col_button:
            st.button(
                "Перейти",
                key=f"entry_button_{entry.id}",
                help="Показать эту запись",
                on_click=lambda e=entry: entry_callback(e),
            )
