# syntax=docker/dockerfile:1
FROM python:3.13-slim

RUN python3.13 -m venv .venv 
#RUN source .venv/bin/activate
RUN python -m pip install --upgrade pip

RUN pip3 install google-adk python-multipart uvicorn

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# --- Install system build deps for wheels (psutil, etc.) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc python3-dev \
 && rm -rf /var/lib/apt/lists/*

# --- Install Python deps ---
# 1) Upgrade pip & install google-adk globally inside the image
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir google-adk

# 2) Copy your own requirements (if any) and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt || true

# --- Copy project code ---
COPY . .

# --- Environment variables (set real values at deploy/run) ---
ENV AGENT_NAME=extractor_agent
ENV GOOGLE_CLOUD_PROJECT="chat-is-this-real-473415"
ENV GOOGLE_CLOUD_LOCATION="us-east1"
ENV GOOGLE_GENAI_USE_VERTEXAI="False"

# Cloud Run sets $PORT; ADK web defaults to 8000
EXPOSE 8000

# Start the ADK server for the chosen agent
CMD ["sh", "-c", "uvicorn your_main_file:api_app --host 0.0.0.0 --port ${PORT:-8000}"]
