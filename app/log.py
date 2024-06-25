import logging

import streamlit as st


def get_session_id():
    if "session_uuid" not in st.session_state:
        return "NO_SESSION_ASSIGNED"

    return st.session_state.session_uuid.hex[:10]


class SessionIdFilter(logging.Filter):
    def filter(self, record):
        record.session_id = get_session_id() if st.session_state else "NO_SESSION"
        return True


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter(fmt="%(module)s: %(asctime)s - %(levelname)s - ID: %(session_id)s - %(message).1000s")

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(log_formatter)
ch.addFilter(SessionIdFilter())

logger.addHandler(ch)
