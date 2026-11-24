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
  # Word lays text out with the active printer's metrics. If the Windows default printer is an
  # unreachable network queue, Word falls back to 96 dpi and snaps every letter to 0.75 pt, so small
  # text looks unevenly spaced. Use a local 600-dpi printer for this Word session only
  # (DoNotSetAsSysDefault = 1 leaves the Windows default printer unchanged).
  try {
    [void][System.__ComObject].InvokeMember("FilePrintSetup", [System.Reflection.BindingFlags]::InvokeMethod, $null, $word.WordBasic, @("Microsoft Print to PDF", 1), $null, $null, @("Printer", "DoNotSetAsSysDefault"))
  } catch { Write-Warning "Could not select Microsoft Print to PDF for this session; letter spacing may be uneven." }
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
