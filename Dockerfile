# KlarSchiff MVP - container for an EU server (see deploy/DEPLOY_EU.md)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 KLARSCHIFF_DATA_DIR=/app/data
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY klarschiff ./klarschiff
COPY mvp ./mvp
COPY evaluation ./evaluation
COPY .streamlit ./.streamlit

# run as a normal user, not root
RUN useradd -m klarschiff && mkdir -p /app/data && chown -R klarschiff /app
USER klarschiff

EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1
CMD ["streamlit", "run", "mvp/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
