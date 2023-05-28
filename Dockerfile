FROM python:3.11-bullseye

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=0 \
    POETRY_VERSION=1.5.0

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock /app/
WORKDIR /app

RUN poetry install --without dev

COPY . .
CMD ["poetry", "run", "python3", "main.py"]
