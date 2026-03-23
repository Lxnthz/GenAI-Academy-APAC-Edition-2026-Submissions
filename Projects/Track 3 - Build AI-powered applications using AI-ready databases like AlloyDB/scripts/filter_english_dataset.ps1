$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$src = Join-Path $root "data\it_support_ticket_sample.csv"
$dst = Join-Path $root "data\it_support_ticket_en.csv"

if (-not (Test-Path $src)) {
    throw "Source dataset not found: $src"
}

$rows = Import-Csv $src | Where-Object { $_.language -eq "en" }
$rows | Export-Csv -Path $dst -NoTypeInformation -Encoding utf8

Write-Output "Wrote cleaned dataset: $dst"
Write-Output "English rows: $($rows.Count)"
