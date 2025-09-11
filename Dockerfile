FROM openjdk:17-jdk-slim

# System Dependencies installieren
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Alle Dateien kopieren
COPY . .

# Maven Wrapper ausführbar machen
RUN chmod +x ./mvnw

# Anwendung kompilieren
RUN ./mvnw clean package -DskipTests

# Port freigeben
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Anwendung starten
CMD ["java", "-jar", "target/pdf-service-1.0.0.jar"]
