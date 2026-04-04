# Stage 1: React TypeScript ビルド
FROM node:20-slim AS frontend
WORKDIR /build
COPY src/frontend/package.json src/frontend/package-lock.json ./
RUN npm ci
COPY src/frontend/ .
RUN npx vite build --outDir /build/dist

# Stage 2: Python API
FROM python:3.11-slim
WORKDIR /app

COPY src/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/config.py .
COPY env/config/application.yml /app/config/application.yml
COPY src/api/ .
COPY --from=frontend /build/dist/ ./static/

ENV CONFIG_PATH=/app/config/application.yml

CMD ["uvicorn", "endpoints.main:app", "--host", "0.0.0.0", "--port", "8080"]
