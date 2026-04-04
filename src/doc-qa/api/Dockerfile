# Build context: プロジェクトルート
# docker build -f src/doc-qa/api/Dockerfile .
FROM python:3.11-slim

WORKDIR /app

COPY src/doc-qa/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/config.py .
COPY env/config/application.yml /app/config/application.yml
COPY src/doc-qa/api/ .

ENV CONFIG_PATH=/app/config/application.yml

CMD ["uvicorn", "endpoints.main:app", "--host", "0.0.0.0", "--port", "8080"]
