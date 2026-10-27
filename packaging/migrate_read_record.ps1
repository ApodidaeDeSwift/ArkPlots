# Remap Read_record.json when plot ids are renumbered.
# Stable key is the plot name in Plotline.json, not the numeric id.
# The record is replaced only after the new mapping is fully built.
# Missing record or missing old plotline is a no-op (fresh install).
param(
    [Parameter(Mandatory = $true)][string]$OldPlotline,
    [Parameter(Mandatory = $true)][string]$NewPlotline,
    [Parameter(Mandatory = $true)][string]$Record
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Write-Fail([string]$Message, [int]$Code) {
    [Console]::Error.WriteLine($Message)
    exit $Code
}

function ConvertTo-JsonToken([string]$Value) {
    $sb = New-Object System.Text.StringBuilder
    foreach ($ch in $Value.ToCharArray()) {
        $code = [int]$ch
        if ($code -eq 34) { [void]$sb.Append('\"') }
        elseif ($code -eq 92) { [void]$sb.Append('\\') }
        elseif ($code -eq 8) { [void]$sb.Append('\b') }
        elseif ($code -eq 9) { [void]$sb.Append('\t') }
        elseif ($code -eq 10) { [void]$sb.Append('\n') }
        elseif ($code -eq 12) { [void]$sb.Append('\f') }
        elseif ($code -eq 13) { [void]$sb.Append('\r') }
        elseif ($code -lt 32) { [void]$sb.AppendFormat('\u{0:x4}', $code) }
        else { [void]$sb.Append($ch) }
    }
    return $sb.ToString()
}

function Read-JsonFile([string]$Path) {
    $text = [System.IO.File]::ReadAllText($Path)
    if (-not $text.Trim()) {
        throw "empty json: $Path"
    }
    return ($text | ConvertFrom-Json)
}

function Get-PlotRows($Document, [string]$Label) {
    $rows = $null
    if ($Document -is [System.Array]) {
        $rows = $Document
    } elseif ($Document.PSObject.Properties.Name -contains 'data') {
        $rows = $Document.data
    }
    if ($null -eq $rows) {
        throw "$Label has no plot array"
    }
    return @($rows)
}

function Get-IdText($Value) {
    return [string]([int64]$Value)
}

if (-not (Test-Path -LiteralPath $Record)) { exit 0 }
if (-not (Test-Path -LiteralPath $OldPlotline)) { exit 0 }
if (-not (Test-Path -LiteralPath $NewPlotline)) {
    Write-Fail "new plotline missing: $NewPlotline" 2
}

$tmp = $Record + '.migrate.tmp'
try {
    $oldRows = Get-PlotRows (Read-JsonFile $OldPlotline) 'old plotline'
    $newRows = Get-PlotRows (Read-JsonFile $NewPlotline) 'new plotline'
    $recordDoc = Read-JsonFile $Record
    if ($recordDoc -is [System.Array]) {
        throw 'read record must be a JSON object'
    }

    $oldIdToName = New-Object 'System.Collections.Generic.Dictionary[string,string]'
    foreach ($row in $oldRows) {
        $name = [string]$row.name
        $id = Get-IdText $row.id
        if (-not $name) { throw "old plotline has an empty name (id $id)" }
        if ($oldIdToName.ContainsKey($id)) { throw "old plotline repeats id $id" }
        if ($oldIdToName.ContainsValue($name)) { throw "old plotline repeats name $name" }
        $oldIdToName.Add($id, $name)
    }

    $nameToNewId = New-Object 'System.Collections.Generic.Dictionary[string,string]'
    foreach ($row in $newRows) {
        $name = [string]$row.name
        $id = Get-IdText $row.id
        if (-not $name) { throw "new plotline has an empty name (id $id)" }
        if ($nameToNewId.ContainsKey($name)) { throw "new plotline repeats name $name" }
        $nameToNewId.Add($name, $id)
    }

    $mapped = New-Object 'System.Collections.Generic.Dictionary[string,string]'
    foreach ($prop in $recordDoc.PSObject.Properties) {
        $oldId = [string]$prop.Name
        if (-not $oldIdToName.ContainsKey($oldId)) { continue }
        $name = $oldIdToName[$oldId]
        if (-not $nameToNewId.ContainsKey($name)) { continue }
        $newId = $nameToNewId[$name]
        if ($mapped.ContainsKey($newId)) {
            throw "read statuses for two plots would land on id $newId"
        }
        $status = $prop.Value
        if ($null -eq $status) { $status = '' }
        $mapped.Add($newId, [string]$status)
    }

    $sorted = @($mapped.Keys | Sort-Object { [int64]$_ })
    $lines = New-Object System.Collections.Generic.List[string]
    [void]$lines.Add('{')
    for ($i = 0; $i -lt $sorted.Count; $i++) {
        $id = [string]$sorted[$i]
        $comma = ''
        if ($i -lt ($sorted.Count - 1)) { $comma = ',' }
        $line = '  "' + (ConvertTo-JsonToken $id) + '": "' + (ConvertTo-JsonToken $mapped[$id]) + '"' + $comma
        [void]$lines.Add($line)
    }
    [void]$lines.Add('}')
    $text = ($lines -join "`r`n") + "`r`n"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($tmp, $text, $utf8)
    [System.IO.File]::Replace($tmp, $Record, [NullString]::Value)
    $tmp = $null
    exit 0
} catch {
    if ($tmp -and (Test-Path -LiteralPath $tmp)) {
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
    }
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
