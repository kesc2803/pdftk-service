# Python 3.11 Base Image
FROM python:3.11-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# System-Pakete aktualisieren
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application Code kopieren
COPY app.py .

# Port freigeben
EXPOSE 8080

# Service starten
CMD ["python", "app.py"]
