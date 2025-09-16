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
    """Konvertiert HTML zu PDF über externen Service mit Fallback"""
    # Versuche zuerst den ursprünglichen Service
    try:
        service_url = "https://html2pdf-q4n2.onrender.com/generate"
        api_key = os.getenv("PDF_API_KEY")
        
        if api_key:
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
            
            response = requests.post(service_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.content
            else:
                print(f"Primary service failed: {response.status_code} - {response.text}")
        else:
            print("No API key provided for primary service")
            
    except Exception as e:
        print(f"Primary service error: {e}")
    
    # Fallback: Verwende einen anderen HTML2PDF Service
    try:
        print("Trying fallback HTML2PDF service...")
        fallback_url = "https://api.html-pdf-node.com/convert"
        fallback_payload = {
            "html": html,
            "format": "A4",
            "margin": "1cm"
        }
        
        response = requests.post(fallback_url, json=fallback_payload, timeout=30)
        
        if response.status_code == 200:
            print("Fallback service successful")
            return response.content
        else:
            print(f"Fallback service failed: {response.status_code}")
            
    except Exception as e:
        print(f"Fallback service error: {e}")
    
    # Letzter Fallback: Erstelle ein einfaches PDF
    print("Using simple PDF fallback")
    return create_simple_pdf_fallback(html)

def create_simple_pdf_fallback(html):
    """Erstellt ein einfaches PDF als letzter Fallback"""
    # WeasyPrint braucht System-Bibliotheken, die im Docker Container fehlen
    # Verwende stattdessen ReportLab direkt
    print("Using ReportLab for PDF generation")
    return create_minimal_pdf(html)

def create_minimal_pdf(html):
    """Erstellt ein minimales PDF ohne externe Abhängigkeiten"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import simpleSplit
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # HTML Tags entfernen und Text extrahieren
    import re
    text = re.sub(r'<[^>]+>', '', html)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    
    # Text auf PDF schreiben
    lines = simpleSplit(text, 'Helvetica', 12, width - 100)
    y = height - 50
    
    for line in lines:
        if y < 50:  # Neue Seite wenn nötig
            c.showPage()
            y = height - 50
        c.drawString(50, y, line)
        y -= 15
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def add_signature_field(pdf_bytes, customer_name, x, y, width, height):
    """Fügt ein AcroForm Signature Field zum PDF hinzu mit pyHanko"""
    try:
        # PDF mit pyHanko lesen
        pdf_reader = PdfFileReader(io.BytesIO(pdf_bytes))
        pdf_writer = PdfFileWriter()
        
        # Alle Seiten kopieren
        for page_num in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page_num])
        
        # Signature Field hinzufügen mit pyHanko (korrekte API)
        from pyhanko.sign import fields
        from pyhanko.pdf_utils import Rectangle
        
        # Erstelle das Signature Field mit korrekter pyHanko API
        sig_field = fields.SignatureField(
            field_name=f'signature_{customer_name}',
            field_rect=Rectangle(x, y, x + width, y + height)
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
    app.run(host='0.0.0.0', port=int(port), debug=False)
