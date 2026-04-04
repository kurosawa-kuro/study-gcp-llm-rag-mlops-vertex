# Build context: プロジェクトルート
# docker build -f src/doc-qa/ingestion/Dockerfile .
FROM python:3.11-slim

WORKDIR /app

COPY src/doc-qa/ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/config.py .
COPY env/config/application.yml /app/config/application.yml
COPY src/doc-qa/ingestion/ .

ENV CONFIG_PATH=/app/config/application.yml

CMD ["python", "main.py"]
