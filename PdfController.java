package com.pdfservice.controller;

import com.pdfservice.service.PdfService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.ByteArrayOutputStream;
import java.time.LocalDateTime;
import java.util.Map;

@RestController
@CrossOrigin(origins = "*")
public class PdfController {

    @Autowired
    private PdfService pdfService;

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        return ResponseEntity.ok(Map.of(
            "status", "OK",
            "service", "Java PDF Service with iText",
            "timestamp", LocalDateTime.now().toString()
        ));
    }

    @GetMapping("/check-itext")
    public ResponseEntity<Map<String, Object>> checkItext() {
        try {
            String version = pdfService.getItextVersion();
            return ResponseEntity.ok(Map.of(
                "available", true,
                "version", version,
                "timestamp", LocalDateTime.now().toString()
            ));
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of(
                "available", false,
                "error", e.getMessage(),
                "timestamp", LocalDateTime.now().toString()
            ));
        }
    }

    @PostMapping(value = "/create-pdf-with-signature", produces = MediaType.APPLICATION_PDF_VALUE)
    public ResponseEntity<byte[]> createPdfWithSignature(@RequestBody Map<String, Object> request) {
        try {
            String html = (String) request.get("html");
            String customerName = (String) request.getOrDefault("customerName", "Kunde");
            Integer signatureX = (Integer) request.getOrDefault("signatureX", 400);
            Integer signatureY = (Integer) request.getOrDefault("signatureY", 50);
            Integer signatureWidth = (Integer) request.getOrDefault("signatureWidth", 100);
            Integer signatureHeight = (Integer) request.getOrDefault("signatureHeight", 50);

            if (html == null || html.trim().isEmpty()) {
                return ResponseEntity.badRequest().build();
            }

            ByteArrayOutputStream pdfBytes = pdfService.createPdfWithSignature(
                html, customerName, signatureX, signatureY, signatureWidth, signatureHeight
            );

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_PDF);
            headers.setContentDispositionFormData("attachment", "document_with_signature.pdf");

            return ResponseEntity.ok()
                .headers(headers)
                .body(pdfBytes.toByteArray());

        } catch (Exception e) {
            return ResponseEntity.status(500).build();
        }
    }

    @PostMapping(value = "/add-signature-field", produces = MediaType.APPLICATION_PDF_VALUE)
    public ResponseEntity<byte[]> addSignatureField(
            @RequestParam("pdf") MultipartFile pdfFile,
            @RequestParam(value = "customerName", defaultValue = "Kunde") String customerName,
            @RequestParam(value = "signatureX", defaultValue = "400") Integer signatureX,
            @RequestParam(value = "signatureY", defaultValue = "50") Integer signatureY,
            @RequestParam(value = "signatureWidth", defaultValue = "100") Integer signatureWidth,
            @RequestParam(value = "signatureHeight", defaultValue = "50") Integer signatureHeight) {
        
        try {
            if (pdfFile.isEmpty()) {
                return ResponseEntity.badRequest().build();
            }

            ByteArrayOutputStream pdfBytes = pdfService.addSignatureField(
                pdfFile.getBytes(), customerName, signatureX, signatureY, signatureWidth, signatureHeight
            );

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_PDF);
            headers.setContentDispositionFormData("attachment", "document_with_signature.pdf");

            return ResponseEntity.ok()
                .headers(headers)
                .body(pdfBytes.toByteArray());

        } catch (Exception e) {
            return ResponseEntity.status(500).build();
        }
    }
}
