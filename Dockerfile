FROM node:24-slim AS frontend
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ backend/
COPY scripts/train_benchmark.py scripts/train_benchmark.py
COPY data/atlas/observations.csv data/atlas/manifest.json data/atlas/storm.json data/atlas/
RUN python scripts/train_benchmark.py
COPY --from=frontend /web/dist frontend/dist/
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
