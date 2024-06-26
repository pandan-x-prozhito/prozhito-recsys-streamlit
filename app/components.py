import re

import streamlit as st

from .data import DiaryEntry

BR_RE = re.compile(r"<br\s*?/?>")
TAG_RE = re.compile(r"<[^>]+>")
SPACES_RE = re.compile(r"\s+")


def clean_entry_text(text: str) -> str:
    """
    Cleans the given text by removing line breaks, HTML tags, and extra spaces.

    Args:
        text (str): The text to be cleaned.

    Returns:
        str: The cleaned text.
    """
    text = BR_RE.sub("\n", text)
    text = TAG_RE.sub("", text)
    text = SPACES_RE.sub(" ", text)
    return text


def diary_card(entry: DiaryEntry, /, tag_callback: callable) -> None:
    """
    Renders a diary card component with the given diary entry.

    Parameters:
        entry (DiaryEntry): The diary entry to display.
        tag_callback (callable): A callback function to handle tag button clicks.

    Returns:
        None
    """
    st.header("Дневниковая запись")

    with st.container(border=True, height=300):
        st.markdown(entry.text, unsafe_allow_html=True)

    st.page_link(
        f"https://corpus.prozhito.org/note/{entry.id}",
        label="Перейти к записи в «Прожито»",
        icon=":material/newspaper:",
    )

    st.subheader("Теги", divider=True)
    tag_cols = st.columns(len(entry.tags), vertical_alignment="center")

    for tag, col in zip(entry.tags, tag_cols):
        with col:
            st.button(
                tag,
                key=f"tag_button_{tag}",
                on_click=lambda t=tag: tag_callback(t),
                help=f'Добавить тег "{tag}" в фильтр',
            )


def diary_snippets(entries: list[DiaryEntry], /, entry_callback: callable) -> None:
    """
    Display snippets of diary entries and provide a button to view the full entry.

    Args:
        entries (list[DiaryEntry]): A list of diary entries.
        entry_callback (callable): A callback function to handle the selected entry.

    Returns:
        None
    """
    if not entries:
        st.warning("Похожих записей не найдено.")
        return
    for entry in entries:
        with st.container(border=True):
            col_text, col_button = st.columns([0.81, 0.19], vertical_alignment="center")

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


def local_css(file_name: str) -> None:
    """
    Applies local CSS styles to a Streamlit app.

    Parameters:
        file_name (str): The path to the CSS file.

    Returns:
        None
    """
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
