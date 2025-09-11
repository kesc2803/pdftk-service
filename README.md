# PDFtk Service README

## Übersicht
Dieser Service bietet PDF-Manipulation mit PDFtk und Unterschriftenfeldern über eine REST API.

## Features
- ✅ PDFtk Integration für echte Unterschriftenfelder
- ✅ HTML zu PDF Konvertierung mit wkhtmltopdf
- ✅ Unterschriftenfelder zu bestehenden PDFs hinzufügen
- ✅ Docker Container für einfache Deployment
- ✅ Health Checks und Error Handling

## API Endpoints

### Health Check
```
GET /health
```

### PDFtk Verfügbarkeit prüfen
```
GET /check-pdftk
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
- Node.js 18+
- PDFtk installiert
- wkhtmltopdf installiert

### Installation
```bash
npm install
npm run dev
```

## Docker Deployment

### Lokal testen
```bash
docker build -t pdftk-service .
docker run -p 3000:3000 pdftk-service
```

### Render.com Deployment
1. Repository zu GitHub pushen
2. Render.com Service erstellen
3. Dockerfile als Build Command verwenden
4. Port 3000 freigeben

## Umgebungsvariablen
- `PORT`: Server Port (default: 3000)
- `NODE_ENV`: Environment (development/production)

## Fehlerbehandlung
- Automatische Cleanup von temporären Dateien
- Detaillierte Error Messages
- Health Checks für Monitoring
