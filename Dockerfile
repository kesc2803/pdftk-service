FROM openjdk:17-jdk-slim

# System Dependencies installieren
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Maven Wrapper kopieren
COPY mvnw .
COPY .mvn .mvn

# Pom.xml kopieren
COPY pom.xml .

# Dependencies herunterladen
RUN ./mvnw dependency:go-offline

# Quellcode kopieren
COPY src src

# Anwendung kompilieren
RUN ./mvnw clean package -DskipTests

# Port freigeben
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Anwendung starten
CMD ["java", "-jar", "target/pdf-service-1.0.0.jar"]
