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
    """Konvertiert HTML zu PDF mit ReportLab (direkt)"""
    print("Using ReportLab for PDF generation")
    return create_simple_pdf_fallback(html)

def create_simple_pdf_fallback(html):
    """Erstellt ein einfaches PDF als letzter Fallback"""
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
    """Fügt ein echtes AcroForm Signature Field zum PDF hinzu mit pyHanko"""
    try:
        print(f"Attempting to add signature field for: {customer_name}")
        
        # PDF mit pyHanko lesen
        pdf_reader = PdfFileReader(io.BytesIO(pdf_bytes))
        pdf_writer = PdfFileWriter()
        
        # Debug: pyHanko Version und API prüfen
        print(f"PdfFileReader attributes: {dir(pdf_reader)}")
        
        # Alle Seiten kopieren (pyHanko API - verschiedene Versionen)
        try:
            # Neue pyHanko API (v0.20+)
            print("Trying new pyHanko API (num_pages)")
            for page_num in range(pdf_reader.num_pages):
                page = pdf_reader.get_page(page_num)
                pdf_writer.add_page(page)
            print("Successfully used new pyHanko API")
        except AttributeError as e:
            print(f"New API failed: {e}")
            try:
                # Alte pyHanko API (v0.19-)
                print("Trying old pyHanko API (pages)")
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    pdf_writer.add_page(page)
                print("Successfully used old pyHanko API")
            except Exception as e2:
                print(f"Old API also failed: {e2}")
                raise e2
        
        # Echtes AcroForm Signature Field erstellen
        from pyhanko.sign import fields
        from pyhanko.pdf_utils import Rectangle
        from pyhanko.pdf_utils.generic import pdf_name
        
        print("Creating signature field...")
        
        # Erstelle ein echtes AcroForm Signature Field
        sig_field = fields.SignatureField(
            field_name=f'signature_{customer_name}',
            field_rect=Rectangle(x, y, x + width, y + height),
            # Wichtig: Stelle sicher, dass es ein echtes AcroForm Field ist
            field_flags=fields.FieldFlag.PRINT | fields.FieldFlag.READ_ONLY,
            field_value=None  # Leeres Field für Unterschrift
        )
        
        # Field zur ersten Seite hinzufügen
        pdf_writer.add_signature_field(sig_field, page_num=0)
        
        # AcroForm aktivieren (wichtig für echte Signature Fields)
        acro_form = pdf_writer.get_acro_form()
        if acro_form:
            acro_form[pdf_name('/SigFlags')] = 3  # SignaturesExist | AppendOnly
        
        # PDF schreiben
        output = io.BytesIO()
        pdf_writer.write(output)
        
        print(f"Successfully added AcroForm signature field: signature_{customer_name}")
        return output.getvalue()
        
    except Exception as e:
        # Fallback: PDF ohne Signature Field zurückgeben
        print(f"Warning: Could not add signature field with pyHanko: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return pdf_bytes

# WSGI Application für Gunicorn
application = app

if __name__ == '__main__':
    port = os.getenv('PORT', '8080')
    print(f"PDF Service starting on port {port}")
    app.run(host='0.0.0.0', port=int(port), debug=False)
