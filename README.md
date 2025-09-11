# Java PDF Service with iText README

## Übersicht
Dieser Service bietet PDF-Manipulation mit Java und iText für echte AcroForm-PDFs mit Unterschriftenfeldern über eine REST API.

## Features
- ✅ **iText 8** für echte AcroForm-PDFs
- ✅ **Spring Boot** Web Framework
- ✅ **Echte interaktive Unterschriftenfelder**
- ✅ **HTML zu PDF** Konvertierung
- ✅ Docker Container für einfache Deployment
- ✅ Health Checks und Error Handling

## API Endpoints

### Health Check
```
GET /health
```

### PDF-Bibliotheken Verfügbarkeit prüfen
```
GET /check-pdf-libs
```

### Unterschriftenfeld zu PDF hinzufügen
```
POST /add-signature-field
Content-Type: multipart/form-data

Body:
- pdf: PDF-Datei (multipart/form-data)
- customerName: Kundenname (optional)
- signatureX: X-Position (default: 400)
- signatureY: Y-Position (default: 50)
- signatureWidth: Breite (default: 100)
- signatureHeight: Höhe (default: 50)
```

### PDF aus HTML mit Unterschriftenfeld erstellen
```
POST /create-pdf-with-signature
Content-Type: application/json

Body:
{
  "html": "<html>...</html>",
  "customerName": "Max Mustermann",
  "signatureX": 400,
  "signatureY": 50,
  "signatureWidth": 100,
  "signatureHeight": 50
}
```

## Lokale Entwicklung

### Voraussetzungen
- Python 3.11+
- pip

### Installation
```bash
pip install -r requirements.txt
python app.py
```

## Docker Deployment

### Lokal testen
```bash
docker build -t python-pdf-service .
docker run -p 3000:3000 python-pdf-service
```

### Render.com Deployment
1. Repository zu GitHub pushen
2. Render.com Service erstellen
3. Dockerfile als Build Command verwenden
4. Port 3000 freigeben

## Umgebungsvariablen
- `PORT`: Server Port (default: 3000)
- `FLASK_ENV`: Environment (development/production)

## Technische Details

### PDF-Erstellung Prozess:
1. **HTML zu PDF** mit WeasyPrint
2. **AcroForm erstellen** mit ReportLab
3. **PDFs mergen** mit PyPDF2
4. **Echte Unterschriftenfelder** im finalen PDF

### Vorteile gegenüber PDFtk:
- ✅ **Keine AcroForm-Probleme**
- ✅ **Zuverlässige PDF-Erstellung**
- ✅ **Echte interaktive Felder**
- ✅ **Bessere HTML-Unterstützung**

## Fehlerbehandlung
- Automatische Cleanup von temporären Dateien
- Detaillierte Error Messages
- Health Checks für Monitoring
