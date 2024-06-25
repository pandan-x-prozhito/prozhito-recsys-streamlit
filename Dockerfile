ARG TAG=3.12-slim

FROM python:${TAG} AS builder

ARG POETRY_VERSION=1.8.3

ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1

# to run poetry directly as soon as it's installed
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN pip install --no-cache-dir poetry==${POETRY_VERSION} 

WORKDIR /app

# copy only pyproject.toml and poetry.lock file nothing else here
COPY poetry.lock pyproject.toml ./

# this will create the folder /app/.venv (might need adjustment depending on which poetry version you are using)
RUN poetry install --no-root --no-ansi --without dev

# ---------------------------------------------------------------------

FROM python:${TAG}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

EXPOSE 80
WORKDIR /app

RUN useradd -m -u 1000 user && chown -R user /app
USER user

# copy the venv folder from builder image 
COPY --from=builder --chown=user /app/.venv ./.venv
COPY --chown=user . .

# download data if it was not copied
ARG DATA_PATH="data/diaries_vec.db"
ARG DATA_DOWNLOAD_URL
RUN python check_and_download_data.py

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]