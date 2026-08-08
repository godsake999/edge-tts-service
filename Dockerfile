FROM python:3.11-slim

# Install dependencies
RUN pip install --no-cache-dir \
    edge-tts \
    fastapi \
    uvicorn

# Copy app
COPY server.py /app/server.py

WORKDIR /app

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
