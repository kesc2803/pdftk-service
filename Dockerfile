FROM openjdk:17-jdk-slim

# System Dependencies installieren
RUN apt-get update && apt-get install -y \
    curl \
    maven \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Alle Dateien kopieren
COPY . .

# Debug: Was wurde kopiert?
RUN echo "=== Alle kopierten Dateien ===" && \
    ls -la && \
    echo "=== src Directory ===" && \
    ls -la src/ || echo "src Directory nicht gefunden" && \
    echo "=== Maven Source Directory ===" && \
    ls -la src/main/java/com/pdfservice/ || echo "Maven Source Directory nicht gefunden"

# Debug: JAR Inhalt überprüfen
RUN echo "=== JAR Inhalt ===" && \
    jar -tf target/pdf-service-1.0.0.jar | head -20 && \
    echo "=== BOOT-INF/classes ===" && \
    jar -tf target/pdf-service-1.0.0.jar | grep "BOOT-INF/classes" | head -10 || echo "Keine BOOT-INF/classes gefunden"

# Port freigeben
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Anwendung starten (mit expliziter Main Class)
CMD ["java", "-cp", "target/pdf-service-1.0.0.jar", "com.pdfservice.PdfServiceApplication"]
