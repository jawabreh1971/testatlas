# ---------- Frontend build ----------
FROM node:20-alpine AS frontend_builder
WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ .
RUN npm run build


# ---------- Backend runtime ----------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=10000  

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source
COPY backend backend

# Replace static with frontend build
RUN rm -rf backend/app/static && mkdir -p backend/app/static
COPY --from=frontend_builder /frontend/dist/ backend/app/static/

# Expose port
EXPOSE $PORT

# Use shell form to allow env var expansion
CMD python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
