# Multi-stage build für Go
FROM golang:1.21-alpine AS builder

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Go Module Dateien kopieren
COPY go.mod ./

# Dependencies herunterladen und go.sum generieren
RUN go mod download && go mod tidy

# Source Code kopieren
COPY main.go ./

# Go Binary kompilieren
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o pdf-service .

# Finales Image
FROM alpine:latest

# curl für Health Check installieren
RUN apk --no-cache add curl

# Arbeitsverzeichnis erstellen
WORKDIR /root/

# Kompiliertes Binary kopieren
COPY --from=builder /app/pdf-service .

# Port freigeben
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/api/health || exit 1

# Anwendung starten
CMD ["./pdf-service"]
