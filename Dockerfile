# PDFtk Service Dockerfile

FROM node:18-alpine

# PDFtk und wkhtmltopdf installieren
RUN apk add --no-cache \
    pdftk \
    wkhtmltopdf \
    fontconfig \
    freetype \
    ttf-dejavu \
    ttf-liberation \
    && rm -rf /var/cache/apk/*

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Package.json kopieren und Dependencies installieren
COPY package*.json ./
RUN npm ci --only=production

# Anwendung kopieren
COPY . .

# Port freigeben
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) })"

# Anwendung starten
CMD ["node", "server.js"]
