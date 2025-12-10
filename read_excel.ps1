chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$path = Get-ChildItem "c:\Users\Chris\OneDrive\*\GitHub\chris\college\Book1.xlsx" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$workbook = $excel.Workbooks.Open($path)

Write-Host "Number of sheets: $($workbook.Sheets.Count)"

foreach ($sheet in $workbook.Sheets) {
    Write-Host ""
    Write-Host "=== SHEET: $($sheet.Name) ==="
    $usedRange = $sheet.UsedRange
    $rows = $usedRange.Rows.Count
    $cols = $usedRange.Columns.Count

    Write-Host "Rows: $rows, Cols: $cols"

    for ($r = 1; $r -le $rows; $r++) {
        $line = @()
        for ($c = 1; $c -le $cols; $c++) {
            $val = $sheet.Cells.Item($r, $c).Text
            if ($val -and $val.Trim()) {
                $line += "$c`:$val"
            }
        }
        if ($line.Count -gt 0) {
            Write-Host "Row $r`: $($line -join ' | ')"
        }
    }
}

$workbook.Close($false)
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
