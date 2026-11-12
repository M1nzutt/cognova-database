FROM python:3.14.10-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/opt/cognova-database

WORKDIR /opt/cognova-database

COPY requirements.lock ./requirements.lock
RUN python -m pip install --require-hashes --no-cache-dir -r requirements.lock

COPY --chown=10001:10001 alembic.ini ./alembic.ini
COPY --chown=10001:10001 cognova_database ./cognova_database
COPY --chown=10001:10001 migrations ./migrations
COPY --chown=10001:10001 scripts/prepare_local_runtime.py ./scripts/prepare_local_runtime.py

USER 10001:10001

CMD ["python", "-m", "cognova_database", "upgrade", "head"]
