# PDF Service with Go + unidoc/unipdf

Ein PDF-Service für die Erstellung von PDFs mit echten AcroForm Signature Fields.

## Technologie Stack

- **Go 1.21**
- **unidoc/unipdf v3.55.0** für PDF-Manipulation und AcroForm-Erstellung
- **Gin** für REST API
- **Docker** für Containerisierung

## Features

- ✅ HTML zu PDF Konvertierung über externen Service
- ✅ Echte AcroForm Signature Fields mit unidoc/unipdf
- ✅ REST API für PDF-Erstellung
- ✅ Health Check Endpoint
- ✅ Einfaches Docker Container (nur Binary)

## API Endpoints

### Health Check
```
GET /api/health
```

### Check unidoc
```
GET /api/check-unidoc
```

### Create PDF with Signature Field
```
POST /api/create-pdf-with-signature
Content-Type: application/json

{
  "html": "<html>...</html>",
  "customerName": "Max Mustermann",
  "signatureX": 400,
  "signatureY": 50,
  "signatureWidth": 100,
  "signatureHeight": 50
}
```

## Umgebungsvariablen

- `PDF_API_KEY`: API Key für den HTML2PDF Service
- `UNIDOC_LICENSE_KEY`: (Optional) Unidoc License Key für kommerzielle Nutzung
- `PORT`: Port für den Service (Standard: 8080)

## Lokale Entwicklung

### Voraussetzungen
- Go 1.21+

### Build und Start
```bash
# Dependencies herunterladen
go mod tidy

# Anwendung starten
go run main.go
```

## Docker Deployment

### Build
```bash
docker build -t pdf-service .
```

### Run
```bash
docker run -p 8080:8080 \
  -e PDF_API_KEY=your_api_key \
  pdf-service
```

## Render.com Deployment

1. Repository mit GitHub verbinden
2. Service Type: Web Service
3. Build Command: `docker build -t pdf-service .`
4. Start Command: `docker run -p $PORT:8080 pdf-service`
5. Umgebungsvariablen setzen:
   - `PDF_API_KEY`: Dein HTML2PDF API Key

## Funktionsweise

1. **HTML zu PDF**: Der Service ruft den externen HTML2PDF Service auf
2. **PDF öffnen**: Das generierte PDF wird mit unidoc/unipdf geöffnet
3. **AcroForm erstellen**: Eine neue AcroForm wird erstellt (falls nicht vorhanden)
4. **Signature Field hinzufügen**: Ein echtes PdfFieldSignature wird zur AcroForm hinzugefügt
5. **PDF speichern**: Das finale PDF mit AcroForm wird zurückgegeben

## Vorteile von Go + unidoc/unipdf

- ✅ Echte AcroForm Signature Fields (nicht nur visuelle)
- ✅ Einfacher Docker Build (Multi-stage)
- ✅ Kleines finales Image (nur Binary)
- ✅ Schnelle Performance
- ✅ Zuverlässige PDF-Standards
- ✅ Keine komplexen Dependencies

## Troubleshooting

### Go Module Issues
Falls Go Module Probleme auftreten:
1. Überprüfe die `go.mod` Datei
2. Führe `go mod tidy` aus
3. Stelle sicher, dass Go 1.21+ verwendet wird

### unidoc/unipdf Dependencies
Falls unidoc/unipdf Dependencies nicht gefunden werden:
1. Überprüfe die Version in `go.mod`
2. Verwende `go mod download` um Dependencies zu überprüfen

### Docker Build Issues
Falls der Docker Build fehlschlägt:
1. Überprüfe die Dockerfile Syntax
2. Stelle sicher, dass alle Go-Dateien korrekt kopiert werden
3. Verwende `docker build --no-cache` für einen sauberen Build
