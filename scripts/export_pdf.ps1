# Export a .docx to PDF with Microsoft Word (Windows). Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File export_pdf.ps1 -Docx C:\full\path\sheet.docx -Pdf C:\full\path\sheet.pdf
# Only opens, exports and closes: querying Styles/Paragraphs through COM before exporting once hung Word for minutes.
param([Parameter(Mandatory = $true)][string]$Docx, [Parameter(Mandatory = $true)][string]$Pdf)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
  $doc = $word.Documents.Open($Docx, $false, $true)
  $doc.ExportAsFixedFormat($Pdf, 17)
  $doc.Close(0)
  "exported: $Pdf"
} finally {
  $word.Quit()
}
