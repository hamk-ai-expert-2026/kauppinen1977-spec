param(
    [string]$Topic,
    [string]$Model = "qwen/qwen3.8-27b",
    [string]$LmStudioUrl = "http://localhost:1234/v1",
    [string]$OutputDirectory = "output",
    [switch]$WithoutSearch
)

$ErrorActionPreference = "Stop"

if (-not $Topic) {
    $Topic = Read-Host "Enter the article topic"
}

Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    py -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
}

$arguments = @(
    "article_generator.py",
    "--topic", $Topic,
    "--model", $Model,
    "--base-url", $LmStudioUrl,
    "--output-dir", $OutputDirectory
)

if ($WithoutSearch) { $arguments += "--without-search" }

& .\.venv\Scripts\python.exe @arguments
exit $LASTEXITCODE
