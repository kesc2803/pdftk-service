package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/unidoc/unipdf/v4/common/license"
	"github.com/unidoc/unipdf/v4/model"
	"github.com/unidoc/unipdf/v4/core"
	"github.com/unidoc/unipdf/v4/creator"
)

type CreatePdfRequest struct {
	HTML            string `json:"html"`
	CustomerName    string `json:"customerName"`
	SignatureX      int    `json:"signatureX"`
	SignatureY      int    `json:"signatureY"`
	SignatureWidth  int    `json:"signatureWidth"`
	SignatureHeight int    `json:"signatureHeight"`
}

type ErrorResponse struct {
	Error   string `json:"error"`
	Details string `json:"details"`
}

func main() {
	// Unidoc License setzen (falls vorhanden)
	if licenseKey := os.Getenv("UNIDOC_LICENSE_KEY"); licenseKey != "" {
		license.SetMeteredKey(licenseKey)
	}

	r := gin.Default()
	r.Use(func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Content-Type")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	// Health Check
	r.GET("/api/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":    "healthy",
			"service":   "PDF Service with unidoc/unipdf v4",
			"timestamp": "2024-01-01T00:00:00Z",
		})
	})

	// Check unidoc
	r.GET("/api/check-unidoc", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status": "unidoc/unipdf v4 available",
			"version": "v4.3.0",
		})
	})

	// Create PDF with signature field
	r.POST("/api/create-pdf-with-signature", func(c *gin.Context) {
		var req CreatePdfRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, ErrorResponse{
				Error:   "Invalid request",
				Details: err.Error(),
			})
			return
		}

		pdfBytes, err := createPdfWithSignatureField(req)
		if err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "Fehler bei der PDF-Erstellung",
				Details: err.Error(),
			})
			return
		}

		c.Header("Content-Type", "application/pdf")
		c.Header("Content-Disposition", "attachment; filename=document_with_signature.pdf")
		c.Data(http.StatusOK, "application/pdf", pdfBytes)
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	fmt.Printf("PDF Service starting on port %s\n", port)
	r.Run(":" + port)
}

func createPdfWithSignatureField(req CreatePdfRequest) ([]byte, error) {
	// Schritt 1: HTML zu PDF konvertieren über externen Service
	pdfBytes, err := convertHTMLToPDF(req.HTML)
	if err != nil {
		return nil, fmt.Errorf("HTML zu PDF Konvertierung fehlgeschlagen: %v", err)
	}

	// Schritt 2: PDF mit unidoc/unipdf öffnen
	pdfReader := bytes.NewReader(pdfBytes)
	reader, err := model.NewPdfReader(pdfReader)
	if err != nil {
		return nil, fmt.Errorf("PDF konnte nicht geöffnet werden: %v", err)
	}

	// Schritt 3: Creator für neues PDF verwenden
	c := creator.New()
	c.SetPageSize(creator.PageSizeA4)

	// Schritt 4: Seiten vom Reader zum Creator kopieren
	numPages, err := reader.GetNumPages()
	if err != nil {
		return nil, fmt.Errorf("Seitenanzahl konnte nicht ermittelt werden: %v", err)
	}

	for i := 1; i <= numPages; i++ {
		page, err := reader.GetPage(i)
		if err != nil {
			return nil, fmt.Errorf("Seite %d konnte nicht gelesen werden: %v", i, err)
		}
		c.AddPage(page)
	}

	// Schritt 5: AcroForm erstellen
	pdfForm := model.NewPdfAcroForm()
	pdfForm.SetNeedAppearances(true)
	c.SetForm(pdfForm)

	// Schritt 6: Signature Field erstellen
	sigField := model.NewPdfFieldSignature(nil)
	sigField.T = core.MakeString("signature_" + req.CustomerName)
	sigField.Rect = core.MakeArray(
		core.MakeFloat(float64(req.SignatureX)),
		core.MakeFloat(float64(req.SignatureY)),
		core.MakeFloat(float64(req.SignatureX + req.SignatureWidth)),
		core.MakeFloat(float64(req.SignatureY + req.SignatureHeight)),
	)
	sigField.Ff = model.FieldFlagRequired

	// Schritt 7: Signature Field dem Formular hinzufügen
	pdfForm.AddField(sigField)

	// Schritt 8: PDF speichern
	var buf bytes.Buffer
	err = c.Write(&buf)
	if err != nil {
		return nil, fmt.Errorf("PDF konnte nicht gespeichert werden: %v", err)
	}

	return buf.Bytes(), nil
}

func convertHTMLToPDF(html string) ([]byte, error) {
	// HTML2PDF Service URL
	serviceURL := "https://html2pdf-q4n2.onrender.com/generate"
	
	// API Key aus Umgebungsvariable
	apiKey := os.Getenv("PDF_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("PDF_API_KEY Umgebungsvariable nicht gesetzt")
	}

	// Request Body
	requestBody := map[string]interface{}{
		"html": html,
		"options": map[string]interface{}{
			"format": "A4",
			"margin": map[string]string{
				"top":    "1cm",
				"bottom": "1cm",
				"left":   "1cm",
				"right":  "1cm",
			},
		},
	}

	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return nil, fmt.Errorf("Request Body konnte nicht erstellt werden: %v", err)
	}

	// HTTP Request
	req, err := http.NewRequest("POST", serviceURL, bytes.NewBuffer(jsonBody))
	if err != nil {
		return nil, fmt.Errorf("HTTP Request konnte nicht erstellt werden: %v", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("x-api-key", apiKey)

	// Request senden
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("HTTP Request fehlgeschlagen: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("HTML2PDF Service Fehler: %d %s", resp.StatusCode, string(body))
	}

	// PDF Bytes lesen
	pdfBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("PDF Response konnte nicht gelesen werden: %v", err)
	}

	return pdfBytes, nil
}
