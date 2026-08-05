FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend /app/backend
COPY frontend /app/frontend
ENV PYTHONPATH=/app/backend DATABASE_PATH=/data/ai_workspaces.db
VOLUME ["/data"]
EXPOSE 8000
CMD ["uvicorn","app.main:app","--app-dir","/app/backend","--host","0.0.0.0","--port","8000"]
