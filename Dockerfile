FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["order-exception-captain-api", "--host", "0.0.0.0", "--database", "data/order-exception-captain.sqlite3"]
