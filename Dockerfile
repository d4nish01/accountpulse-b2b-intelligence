# Single-image deploy: builds the React frontend, then serves it from FastAPI.
# One container = UI + API + sample data. Render/Fly/any Docker host works.

# Stage 1: build the frontend
FROM node:20-slim AS frontend
WORKDIR /fe
COPY frontend/package.json .
RUN npm install
COPY frontend/ .
# Empty API base = call the same origin that served the page.
ENV VITE_API_BASE=""
RUN npm run build

# Stage 2: backend runtime
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY sample_data /sample_data
COPY --from=frontend /fe/dist ./static
ENV STATIC_DIR=/app/static
# SQLite file lives in the container; fine for a demo deploy.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
