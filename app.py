from flask import Flask, request, jsonify, send_file
import requests
import io
import os
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.pdf_utils.writer import PdfFileWriter

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "pdf-service"})

@app.route('/create-pdf', methods=['POST'])
def create_pdf():
    try:
        data = request.get_json()
        
        # Validierung
        required_fields = ['html', 'customerName', 'signatureX', 'signatureY', 'signatureWidth', 'signatureHeight']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # HTML zu PDF konvertieren
        pdf_bytes = convert_html_to_pdf(data['html'])
        
        # Signature Field hinzufügen
        pdf_with_signature = add_signature_field(
            pdf_bytes,
            data['customerName'],
            data['signatureX'],
            data['signatureY'],
            data['signatureWidth'],
            data['signatureHeight']
        )
        
        return send_file(
            io.BytesIO(pdf_with_signature),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{data['customerName']}_document.pdf"
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def convert_html_to_pdf(html):
    """Konvertiert HTML zu PDF über externen Service"""
    service_url = "https://html2pdf-q4n2.onrender.com/generate"
    api_key = os.getenv("PDF_API_KEY")
    
    if not api_key:
        raise Exception("PDF_API_KEY environment variable not set")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "html": html,
        "options": {
            "format": "A4",
            "margin": {
                "top": "1cm",
                "right": "1cm",
                "bottom": "1cm",
                "left": "1cm"
            }
        }
    }
    
    response = requests.post(service_url, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"HTML to PDF conversion failed: {response.status_code} - {response.text}")
    
    return response.content

def add_signature_field(pdf_bytes, customer_name, x, y, width, height):
    """Fügt ein AcroForm Signature Field zum PDF hinzu mit pyHanko"""
    try:
        # PDF mit pyHanko lesen
        pdf_reader = PdfFileReader(io.BytesIO(pdf_bytes))
        pdf_writer = PdfFileWriter()
        
        # Alle Seiten kopieren
        for page_num in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page_num])
        
        # Signature Field hinzufügen mit pyHanko
        from pyhanko.sign import fields
        
        sig_field = fields.SignatureField(
            name=f'signature_{customer_name}',
            field_name=f'signature_{customer_name}',
            field_rect=(x, y, x + width, y + height),
            field_value=None
        )
        
        # Field zur ersten Seite hinzufügen
        pdf_writer.add_signature_field(sig_field, page_num=0)
        
        # PDF schreiben
        output = io.BytesIO()
        pdf_writer.write(output)
        return output.getvalue()
        
    except Exception as e:
        # Fallback: PDF ohne Signature Field zurückgeben
        print(f"Warning: Could not add signature field with pyHanko: {e}")
        return pdf_bytes

if __name__ == '__main__':
    port = os.getenv('PORT', '8080')
    print(f"PDF Service starting on port {port}")
    app.run(host='0.0.0.0', port=int(port))
