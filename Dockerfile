# ---------- Frontend build ----------
FROM node:20-alpine AS frontend_builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---------- Backend runtime ----------
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/app /app/backend/app
COPY backend/data /app/backend/data

# Copy frontend dist into backend static
RUN rm -rf /app/backend/app/static && mkdir -p /app/backend/app/static
COPY --from=frontend_builder /app/dist/ /app/backend/app/static/

ENV PORT=8080
EXPOSE 8080
CMD ["python","-m","uvicorn","backend.app.main:app","--host","0.0.0.0","--port","8080"]
