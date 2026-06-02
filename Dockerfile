FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

RUN useradd --create-home --uid 1000 botuser \
    && mkdir -p /data \
    && chown -R botuser:botuser /app /data
USER botuser

ENV DB_PATH=/data/imagebot.db

CMD ["python", "-m", "app.main"]
