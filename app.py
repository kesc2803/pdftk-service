from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tempfile
import os
import io
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfform
from reportlab.lib.colors import black
import PyPDF2
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import requests
import logging

app = Flask(__name__)
CORS(app)

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'OK',
        'service': 'Python PDF Service with AcroForm',
        'timestamp': str(datetime.now())
    })

@app.route('/check-pdf-libs', methods=['GET'])
def check_pdf_libs():
    try:
        # Prüfe ob alle Bibliotheken verfügbar sind
        import PyPDF2
        import reportlab
        
        return jsonify({
            'available': True,
            'libraries': {
                'PyPDF2': PyPDF2.__version__,
                'reportlab': reportlab.Version
            },
            'timestamp': str(datetime.now())
        })
    except Exception as error:
        return jsonify({
            'available': False,
            'error': str(error),
            'timestamp': str(datetime.now())
        }), 500

@app.route('/create-pdf-with-signature', methods=['POST'])
def create_pdf_with_signature():
    try:
        data = request.get_json()
        html_content = data.get('html')
        customer_name = data.get('customerName', 'Kunde')
        signature_x = int(data.get('signatureX', 400))
        signature_y = int(data.get('signatureY', 50))
        signature_width = int(data.get('signatureWidth', 100))
        signature_height = int(data.get('signatureHeight', 50))
        
        if not html_content:
            return jsonify({'error': 'Kein HTML-Content bereitgestellt'}), 400
        
        logger.info(f'Erstelle PDF mit Unterschriftenfeld für {customer_name}')
        
        # Schritt 1: HTML zu PDF konvertieren mit externem Service
        pdf_buffer = convert_html_to_pdf(html_content)
        
        # Schritt 2: AcroForm mit Unterschriftenfeld erstellen
        acroform_pdf = create_acroform_with_signature(
            pdf_buffer, 
            customer_name, 
            signature_x, 
            signature_y, 
            signature_width, 
            signature_height
        )
        
        # Schritt 3: PDF als Response senden
        acroform_pdf.seek(0)
        
        return send_file(
            acroform_pdf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='document_with_signature.pdf'
        )
        
    except Exception as error:
        logger.error(f'Fehler bei PDF-Erstellung: {str(error)}')
        return jsonify({
            'error': 'Fehler bei der PDF-Erstellung',
            'details': str(error)
        }), 500

def convert_html_to_pdf(html_content):
    """
    Konvertiert HTML zu PDF mit externem Service
    """
    try:
        # Verwende den bestehenden HTML2PDF Service
        api_key = os.environ.get('PDF_API_KEY', '')
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key
        }
        
        response = requests.post(
            'https://html2pdf-q4n2.onrender.com/generate',
            json={'html': html_content},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            pdf_buffer = io.BytesIO(response.content)
            pdf_buffer.seek(0)
            logger.info('HTML erfolgreich zu PDF konvertiert')
            return pdf_buffer
        else:
            raise Exception(f'HTML2PDF Service Fehler: {response.status_code}')
            
    except Exception as error:
        logger.error(f'Fehler bei HTML zu PDF Konvertierung: {str(error)}')
        raise error

def create_acroform_with_signature(pdf_buffer, customer_name, x, y, width, height):
    """
    Erstellt ein AcroForm-PDF mit Unterschriftenfeld
    """
    try:
        # Lese das ursprüngliche PDF
        pdf_reader = PyPDF2.PdfReader(pdf_buffer)
        
        # Erstelle ein neues PDF mit ReportLab für das AcroForm
        output_buffer = io.BytesIO()
        c = canvas.Canvas(output_buffer, pagesize=A4)
        
        # Erstelle AcroForm-Felder
        c.acroForm.textfield(
            name='customerName',
            tooltip='Kundenname',
            x=x, y=y-30, width=width, height=20,
            borderColor=black,
            fillColor=None,
            textColor=black,
            fontSize=10,
            value=customer_name
        )
        
        c.acroForm.signature(
            name='signature',
            tooltip='Unterschrift',
            x=x, y=y, width=width, height=height,
            borderColor=black,
            fillColor=None,
            textColor=black
        )
        
        c.save()
        output_buffer.seek(0)
        
        # Merge das ursprüngliche PDF mit dem AcroForm
        acroform_reader = PyPDF2.PdfReader(output_buffer)
        
        # Erstelle Writer für das finale PDF
        writer = PyPDF2.PdfWriter()
        
        # Füge Seiten vom ursprünglichen PDF hinzu
        for page in pdf_reader.pages:
            writer.add_page(page)
        
        # Füge AcroForm-Felder hinzu
        if acroform_reader.pages:
            acroform_page = acroform_reader.pages[0]
            writer.add_page(acroform_page)
        
        # Schreibe das finale PDF
        final_buffer = io.BytesIO()
        writer.write(final_buffer)
        final_buffer.seek(0)
        
        logger.info('AcroForm mit Unterschriftenfeld erfolgreich erstellt')
        return final_buffer
        
    except Exception as error:
        logger.error(f'Fehler beim Erstellen des AcroForms: {str(error)}')
        raise error

@app.route('/add-signature-field', methods=['POST'])
def add_signature_field():
    try:
        if 'pdf' not in request.files:
            return jsonify({'error': 'Keine PDF-Datei hochgeladen'}), 400
        
        pdf_file = request.files['pdf']
        customer_name = request.form.get('customerName', 'Kunde')
        signature_x = int(request.form.get('signatureX', 400))
        signature_y = int(request.form.get('signatureY', 50))
        signature_width = int(request.form.get('signatureWidth', 100))
        signature_height = int(request.form.get('signatureHeight', 50))
        
        # Lese PDF-Datei
        pdf_buffer = io.BytesIO()
        pdf_file.save(pdf_buffer)
        pdf_buffer.seek(0)
        
        # Erstelle AcroForm mit Unterschriftenfeld
        acroform_pdf = create_acroform_with_signature(
            pdf_buffer,
            customer_name,
            signature_x,
            signature_y,
            signature_width,
            signature_height
        )
        
        acroform_pdf.seek(0)
        
        return send_file(
            acroform_pdf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='document_with_signature.pdf'
        )
        
    except Exception as error:
        logger.error(f'Fehler bei PDF-Verarbeitung: {str(error)}')
        return jsonify({
            'error': 'Fehler bei der PDF-Verarbeitung',
            'details': str(error)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint nicht gefunden'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Interner Serverfehler: {str(error)}')
    return jsonify({'error': 'Interner Serverfehler'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)
