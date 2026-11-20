# Export a .docx to PDF with Microsoft Word (Windows). Usage (relative or absolute paths):
#   powershell -NoProfile -ExecutionPolicy Bypass -File export_pdf.ps1 -Docx sheet.docx -Pdf sheet.pdf
# Only opens, exports and closes: querying Styles/Paragraphs through COM before exporting once hung Word for minutes.
param([Parameter(Mandatory = $true)][string]$Docx, [Parameter(Mandatory = $true)][string]$Pdf)
$ErrorActionPreference = "Stop"
# Word resolves relative paths against its own folder (e.g. C:\Windows\system32), so pass it full paths.
$here = (Get-Location).ProviderPath
$Docx = [IO.Path]::GetFullPath([IO.Path]::Combine($here, $Docx))
$Pdf = [IO.Path]::GetFullPath([IO.Path]::Combine($here, $Pdf))
if (-not (Test-Path -LiteralPath $Docx)) { throw "Not found: $Docx" }
try {
  $word = New-Object -ComObject Word.Application
} catch {
  throw "Microsoft Word is not available; open the .docx in Word (or another editor) and export the PDF by hand."
}
$word.Visible = $false
$word.DisplayAlerts = 0
try {
  $doc = $word.Documents.Open($Docx, $false, $true)
  try {
    $doc.ExportAsFixedFormat($Pdf, 17)
  } catch {
    throw "Export failed for $Pdf - if the PDF is open in a viewer, close it and run again. ($($_.Exception.Message))"
  } finally {
    $doc.Close(0)
  }
  "exported: $Pdf"
} finally {
  $word.Quit()
}
