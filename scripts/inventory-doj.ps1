param([string]$OutputDirectory = (Join-Path $PSScriptRoot ('../data/inventory/' + (Get-Date -Format 'yyyy-MM-dd'))))
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$base = 'https://www.justice.gov'
$rows = @()
$observations = @()
$failures = @()
$contextPages = @()
foreach ($contextUrl in @('https://www.justice.gov/epstein', 'https://www.justice.gov/epstein/doj-disclosures')) {
    try {
        $contextResponse = Invoke-WebRequest -Uri $contextUrl -TimeoutSec 60
        $contextSnapshot = 'context-' + ([uri]$contextUrl).Segments[-1] + '.html'
        [IO.File]::WriteAllText((Join-Path $OutputDirectory $contextSnapshot), $contextResponse.Content)
        $contextPages += [pscustomobject]@{url=$contextUrl; retrieved_at_utc=[DateTime]::UtcNow.ToString('o'); snapshot=$contextSnapshot; html_sha256=(Get-FileHash (Join-Path $OutputDirectory $contextSnapshot) -Algorithm SHA256).Hash.ToLower()}
    } catch {
        $failures += [pscustomobject]@{url=$contextUrl; error=$_.Exception.Message; retrieved_at_utc=[DateTime]::UtcNow.ToString('o')}
    }
}
function Read-Listing([string]$url) {
    $response = Invoke-WebRequest -Uri $url -TimeoutSec 60
    $html = $response.Content
    $links = @([regex]::Matches($html, '<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', 'Singleline') | ForEach-Object {
        $href = [System.Net.WebUtility]::HtmlDecode($_.Groups[1].Value)
        if ($href -match '/epstein/files/') {
            [pscustomobject]@{ url = ([uri]::new([uri]$url, $href)).AbsoluteUri; filename = [uri]::UnescapeDataString(($href -split '/')[-1]) }
        }
    } | Sort-Object url -Unique)
    if ($links.Count -eq 0) { throw "No file links found at $url; review access or markup before trusting results." }
    $pages = @([regex]::Matches($html, '[?&]page=(\d+)') | ForEach-Object { [int]$_.Groups[1].Value })
    $last = if ($pages.Count) { ($pages | Measure-Object -Maximum).Maximum } else { 0 }
    $snapshot = 'listing-' + ([uri]$url).Segments[-1] + '-page-' + $(if (([uri]$url).Query) { ([uri]$url).Query -replace '\D', '' } else { '0' }) + '.html'
    [System.IO.File]::WriteAllText((Join-Path $OutputDirectory $snapshot), $html)
    $script:observations += [pscustomobject]@{url=$url; retrieved_at_utc=[DateTime]::UtcNow.ToString('o'); status=[int]$response.StatusCode; snapshot=$snapshot; html_sha256=(Get-FileHash (Join-Path $OutputDirectory $snapshot) -Algorithm SHA256).Hash.ToLower(); listed_file_count=$links.Count; file_links=$links; archive_links=@([regex]::Matches($html, 'href="([^"]+\.zip(?:\?[^"]*)?)"') | ForEach-Object {$_.Groups[1].Value})}
    return [pscustomobject]@{links=$links; last=[int]$last}
}
foreach ($id in 1..12) {
    $url = "$base/epstein/doj-disclosures/data-set-$id-files"
    try { $first = Read-Listing $url } catch {
        $failures += [pscustomobject]@{url=$url; error=$_.Exception.Message; retrieved_at_utc=[DateTime]::UtcNow.ToString('o')}
        Write-Warning "Dataset $id first page unavailable"
        continue
    }
    $last = $null
    if ($first.last -gt 0) {
        $lastUrl = $url + '?page=' + $first.last
        try { Start-Sleep -Milliseconds 300; $last = Read-Listing $lastUrl } catch {
            $failures += [pscustomobject]@{url=$lastUrl; error=$_.Exception.Message; retrieved_at_utc=[DateTime]::UtcNow.ToString('o')}
        }
    } else { $last = $first }
    $observed = @(@($first.links.url) + @($last.links.url) | Where-Object { $_ } | Sort-Object -Unique)
    $rows += [pscustomobject]@{
        dataset=$id; listing_url=$url; listing_pages=$first.last+1
        first_page_files=$first.links.Count; last_page_files=$(if ($last) {$last.links.Count} else {$null})
        pagination_implied_files=$(if ($last) {($first.last * $first.links.Count)+$last.links.Count} else {$null})
        count_status=$(if (-not $last) {'last_page_unavailable_total_unknown'} elseif ($first.last -le 1) {'all_listing_pages_observed'} else {'estimate_assumes_uniform_intermediate_pages'})
        unique_file_urls_observed=$observed.Count
        first_listed_filename=$first.links[0].filename; last_listed_filename=$(if ($last) {$last.links[-1].filename} else {$null})
        extensions_observed=(@($first.links.filename + $last.links.filename | Where-Object { $_ } | ForEach-Object {[IO.Path]::GetExtension($_).ToLower()} | Sort-Object -Unique) -join ',')
        document_bytes=$null; document_pages=$null; document_dates=$null; ocr_quality=$null; document_hashes=$null
    }
    Write-Host "Dataset $id : $($first.last+1) advertised listing pages; $($observed.Count) unique file URLs observed"
    Start-Sleep -Milliseconds 300
}
$rows | Export-Csv (Join-Path $OutputDirectory 'datasets.csv') -NoTypeInformation -Encoding utf8
@{scope='Context pages and first/last dataset listing pages only; no document bodies or HEAD requests'; retrieved_at_utc=[DateTime]::UtcNow.ToString('o'); datasets=$rows; observations=$observations; context_pages=$contextPages; failures=$failures} | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $OutputDirectory 'inventory.json') -Encoding utf8
$observations | ForEach-Object {
    $observation = $_
    foreach ($file in $observation.file_links) {
        [pscustomobject]@{dataset=[int]([regex]::Match($observation.url, 'data-set-(\d+)').Groups[1].Value); file_id=[IO.Path]::GetFileNameWithoutExtension($file.filename); filename=$file.filename; url=$file.url; listing_url=$observation.url; observed_at_utc=$observation.retrieved_at_utc}
    }
} | Sort-Object dataset,url -Unique | Export-Csv (Join-Path $OutputDirectory 'observed-files.csv') -NoTypeInformation -Encoding utf8
