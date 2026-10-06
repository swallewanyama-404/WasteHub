FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt

RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY scripts /app/scripts

RUN mkdir -p /app/media/evidence

EXPOSE 8000

CMD ["sh", "-c", "python -m alembic -c backend/alembic.ini upgrade head && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
