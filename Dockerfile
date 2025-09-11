FROM openjdk:17-jdk-slim

# System Dependencies installieren
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Alle Dateien kopieren
COPY . .

# Maven Wrapper ausführbar machen und JAR herunterladen
RUN chmod +x ./mvnw && \
    mkdir -p .mvn/wrapper && \
    curl -o .mvn/wrapper/maven-wrapper.jar https://repo.maven.apache.org/maven2/org/apache/maven/wrapper/maven-wrapper/3.1.0/maven-wrapper-3.1.0.jar && \
    echo "distributionUrl=https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/3.9.6/apache-maven-3.9.6-bin.zip" > .mvn/wrapper/maven-wrapper.properties && \
    echo "wrapperUrl=https://repo.maven.apache.org/maven2/org/apache/maven/wrapper/maven-wrapper/3.1.0/maven-wrapper-3.1.0.jar" >> .mvn/wrapper/maven-wrapper.properties

# Anwendung kompilieren
RUN ./mvnw clean package -DskipTests

# Port freigeben
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Anwendung starten
CMD ["java", "-jar", "target/pdf-service-1.0.0.jar"]
