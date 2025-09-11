const express = require('express');
const multer = require('multer');
const cors = require('cors');
const helmet = require('helmet');
const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const { promisify } = require('util');

const execAsync = promisify(exec);
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Multer für Datei-Uploads
const upload = multer({ 
  storage: multer.memoryStorage(),
  limits: { fileSize: 50 * 1024 * 1024 } // 50MB limit
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    service: 'PDFtk Service',
    timestamp: new Date().toISOString()
  });
});

// PDFtk verfügbar prüfen
app.get('/check-pdftk', async (req, res) => {
  try {
    const { stdout } = await execAsync('pdftk --version');
    res.json({ 
      available: true, 
      version: stdout.trim(),
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ 
      available: false, 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Unterschriftenfeld zu PDF hinzufügen
app.post('/add-signature-field', upload.single('pdf'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'Keine PDF-Datei hochgeladen' });
    }

    const { customerName, signatureX = 400, signatureY = 50, signatureWidth = 100, signatureHeight = 50 } = req.body;
    
    // Temporäre Dateien erstellen
    const tempDir = '/tmp';
    const timestamp = Date.now();
    const inputPath = path.join(tempDir, `input_${timestamp}.pdf`);
    const outputPath = path.join(tempDir, `output_${timestamp}.pdf`);
    const fdfPath = path.join(tempDir, `form_${timestamp}.fdf`);

    try {
      // PDF-Datei speichern
      await fs.writeFile(inputPath, req.file.buffer);

      // FDF-Datei für Unterschriftenfeld erstellen
      const fdfContent = `%FDF-1.2
1 0 obj
<<
/FDF
<<
/Fields
[
<<
/T (signature)
/Rect [${signatureX} ${signatureY} ${parseInt(signatureX) + parseInt(signatureWidth)} ${parseInt(signatureY) + parseInt(signatureHeight)}]
/FT /Sig
/Ff 1
>>
<<
/T (customerName)
/Rect [${signatureX} ${parseInt(signatureY) - 30} ${parseInt(signatureX) + parseInt(signatureWidth)} ${parseInt(signatureY) - 10}]
/V (${customerName || 'Kunde'})
/FT /Tx
/Ff 1
>>
]
>>
>>
endobj
trailer
<<
/Root 1 0 R
>>
%%EOF`;

      await fs.writeFile(fdfPath, fdfContent);

      // PDFtk ausführen
      const command = `pdftk "${inputPath}" fill_form "${fdfPath}" output "${outputPath}" flatten`;
      console.log('Executing PDFtk command:', command);
      
      const { stdout, stderr } = await execAsync(command);
      
      if (stderr && !stderr.includes('Success')) {
        console.warn('PDFtk warning:', stderr);
      }

      // Ergebnis lesen
      const resultPdf = await fs.readFile(outputPath);

      // Temporäre Dateien löschen
      await Promise.all([
        fs.unlink(inputPath).catch(() => {}),
        fs.unlink(outputPath).catch(() => {}),
        fs.unlink(fdfPath).catch(() => {})
      ]);

      // PDF als Response senden
      res.setHeader('Content-Type', 'application/pdf');
      res.setHeader('Content-Disposition', 'attachment; filename="document_with_signature.pdf"');
      res.send(resultPdf);

    } catch (error) {
      // Cleanup bei Fehler
      await Promise.all([
        fs.unlink(inputPath).catch(() => {}),
        fs.unlink(outputPath).catch(() => {}),
        fs.unlink(fdfPath).catch(() => {})
      ]);
      
      throw error;
    }

  } catch (error) {
    console.error('Fehler bei PDFtk Verarbeitung:', error);
    res.status(500).json({ 
      error: 'Fehler bei der PDF-Verarbeitung',
      details: error.message 
    });
  }
});

// PDF aus HTML erstellen und Unterschriftenfeld hinzufügen
app.post('/create-pdf-with-signature', async (req, res) => {
  try {
    const { html, customerName, signatureX = 400, signatureY = 50, signatureWidth = 100, signatureHeight = 50 } = req.body;
    
    if (!html) {
      return res.status(400).json({ error: 'Kein HTML-Content bereitgestellt' });
    }

    // Temporäre Dateien
    const tempDir = '/tmp';
    const timestamp = Date.now();
    const htmlPath = path.join(tempDir, `input_${timestamp}.html`);
    const pdfPath = path.join(tempDir, `intermediate_${timestamp}.pdf`);
    const outputPath = path.join(tempDir, `output_${timestamp}.pdf`);
    const fdfPath = path.join(tempDir, `form_${timestamp}.fdf`);

    try {
      // HTML-Datei speichern
      await fs.writeFile(htmlPath, html);

      // HTML zu PDF konvertieren mit wkhtmltopdf
      const wkhtmlCommand = `wkhtmltopdf --page-size A4 --margin-top 1cm --margin-bottom 1cm --margin-left 1cm --margin-right 1cm "${htmlPath}" "${pdfPath}"`;
      console.log('Executing wkhtmltopdf command:', wkhtmlCommand);
      
      await execAsync(wkhtmlCommand);

      // FDF-Datei für Unterschriftenfeld erstellen
      const fdfContent = `%FDF-1.2
1 0 obj
<<
/FDF
<<
/Fields
[
<<
/T (signature)
/Rect [${signatureX} ${signatureY} ${parseInt(signatureX) + parseInt(signatureWidth)} ${parseInt(signatureY) + parseInt(signatureHeight)}]
/FT /Sig
/Ff 1
>>
<<
/T (customerName)
/Rect [${signatureX} ${parseInt(signatureY) - 30} ${parseInt(signatureX) + parseInt(signatureWidth)} ${parseInt(signatureY) - 10}]
/V (${customerName || 'Kunde'})
/FT /Tx
/Ff 1
>>
]
>>
>>
endobj
trailer
<<
/Root 1 0 R
>>
%%EOF`;

      await fs.writeFile(fdfPath, fdfContent);

      // PDFtk ausführen
      const pdftkCommand = `pdftk "${pdfPath}" fill_form "${fdfPath}" output "${outputPath}" flatten`;
      console.log('Executing PDFtk command:', pdftkCommand);
      
      const { stdout, stderr } = await execAsync(pdftkCommand);
      
      if (stderr && !stderr.includes('Success')) {
        console.warn('PDFtk warning:', stderr);
      }

      // Ergebnis lesen
      const resultPdf = await fs.readFile(outputPath);

      // Temporäre Dateien löschen
      await Promise.all([
        fs.unlink(htmlPath).catch(() => {}),
        fs.unlink(pdfPath).catch(() => {}),
        fs.unlink(outputPath).catch(() => {}),
        fs.unlink(fdfPath).catch(() => {})
      ]);

      // PDF als Response senden
      res.setHeader('Content-Type', 'application/pdf');
      res.setHeader('Content-Disposition', 'attachment; filename="document_with_signature.pdf"');
      res.send(resultPdf);

    } catch (error) {
      // Cleanup bei Fehler
      await Promise.all([
        fs.unlink(htmlPath).catch(() => {}),
        fs.unlink(pdfPath).catch(() => {}),
        fs.unlink(outputPath).catch(() => {}),
        fs.unlink(fdfPath).catch(() => {})
      ]);
      
      throw error;
    }

  } catch (error) {
    console.error('Fehler bei PDF-Erstellung mit Unterschriftenfeld:', error);
    res.status(500).json({ 
      error: 'Fehler bei der PDF-Erstellung',
      details: error.message 
    });
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error);
  res.status(500).json({ 
    error: 'Interner Serverfehler',
    details: process.env.NODE_ENV === 'development' ? error.message : 'Unbekannter Fehler'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Endpoint nicht gefunden' });
});

app.listen(PORT, () => {
  console.log(`PDFtk Service läuft auf Port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`PDFtk check: http://localhost:${PORT}/check-pdftk`);
});
