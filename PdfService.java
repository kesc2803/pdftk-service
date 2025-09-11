package com.pdfservice.service;

import com.itextpdf.html2pdf.HtmlConverter;
import com.itextpdf.forms.PdfAcroForm;
import com.itextpdf.forms.fields.PdfFormField;
import com.itextpdf.forms.fields.PdfTextFormField;
import com.itextpdf.forms.fields.PdfSignatureFormField;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfReader;
import com.itextpdf.kernel.pdf.PdfWriter;
import com.itextpdf.layout.Document;
import com.itextpdf.layout.element.Paragraph;
import com.itextpdf.layout.properties.TextAlignment;
import org.springframework.stereotype.Service;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

@Service
public class PdfService {

    public String getItextVersion() {
        return "iText 8.0.2";
    }

    public ByteArrayOutputStream createPdfWithSignature(String html, String customerName, 
            int signatureX, int signatureY, int signatureWidth, int signatureHeight) throws IOException {
        
        // Schritt 1: HTML zu PDF konvertieren
        ByteArrayOutputStream htmlPdfBytes = convertHtmlToPdf(html);
        
        // Schritt 2: AcroForm mit Unterschriftenfeld hinzufügen
        return addAcroFormToPdf(htmlPdfBytes.toByteArray(), customerName, 
                signatureX, signatureY, signatureWidth, signatureHeight);
    }

    public ByteArrayOutputStream addSignatureField(byte[] pdfBytes, String customerName,
            int signatureX, int signatureY, int signatureWidth, int signatureHeight) throws IOException {
        
        return addAcroFormToPdf(pdfBytes, customerName, signatureX, signatureY, signatureWidth, signatureHeight);
    }

    private ByteArrayOutputStream convertHtmlToPdf(String html) throws IOException {
        try {
            // Verwende externen HTML2PDF Service
            String apiKey = System.getenv("PDF_API_KEY");
            if (apiKey == null || apiKey.trim().isEmpty()) {
                throw new IOException("PDF_API_KEY environment variable not set");
            }

            CloseableHttpClient httpClient = HttpClients.createDefault();
            HttpPost httpPost = new HttpPost("https://html2pdf-q4n2.onrender.com/generate");
            
            httpPost.setHeader("Content-Type", "application/json");
            httpPost.setHeader("x-api-key", apiKey);
            
            String jsonPayload = "{\"html\":\"" + html.replace("\"", "\\\"") + "\"}";
            httpPost.setEntity(new StringEntity(jsonPayload, StandardCharsets.UTF_8));

            try (CloseableHttpClient client = httpClient) {
                var response = client.execute(httpPost);
                if (response.getStatusLine().getStatusCode() == 200) {
                    byte[] pdfBytes = EntityUtils.toByteArray(response.getEntity());
                    ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
                    outputStream.write(pdfBytes);
                    return outputStream;
                } else {
                    throw new IOException("HTML2PDF Service error: " + response.getStatusLine().getStatusCode());
                }
            }
        } catch (Exception e) {
            throw new IOException("Failed to convert HTML to PDF: " + e.getMessage(), e);
        }
    }

    private ByteArrayOutputStream addAcroFormToPdf(byte[] pdfBytes, String customerName,
            int signatureX, int signatureY, int signatureWidth, int signatureHeight) throws IOException {
        
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        
        try (PdfReader reader = new PdfReader(new ByteArrayInputStream(pdfBytes));
             PdfWriter writer = new PdfWriter(outputStream);
             PdfDocument pdfDoc = new PdfDocument(reader, writer)) {
            
            // Erstelle AcroForm
            PdfAcroForm form = PdfAcroForm.getAcroForm(pdfDoc, true);
            
            // Erstelle Textfeld für Kundenname
            PdfTextFormField customerNameField = PdfFormField.createText(
                pdfDoc, signatureX, signatureY - 30, signatureWidth, 20, "customerName"
            );
            customerNameField.setValue(customerName);
            customerNameField.setReadOnly(true);
            form.addField(customerNameField);
            
            // Erstelle Unterschriftenfeld
            PdfSignatureFormField signatureField = PdfFormField.createSignature(
                pdfDoc, signatureX, signatureY, signatureWidth, signatureHeight, "signature"
            );
            form.addField(signatureField);
            
            // Erstelle zusätzliches Textfeld für manuelle Unterschrift
            PdfTextFormField manualSignatureField = PdfFormField.createText(
                pdfDoc, signatureX, signatureY - 60, signatureWidth, 20, "manualSignature"
            );
            manualSignatureField.setValue("");
            form.addField(manualSignatureField);
        }
        
        return outputStream;
    }
}
