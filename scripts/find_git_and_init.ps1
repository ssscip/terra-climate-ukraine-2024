<#!
Purpose: Locate git.exe on drive D:, add to PATH for this session, then initialize and push repository.
Usage:
  pwsh -File scripts/find_git_and_init.ps1 -GitHubUser YOUR_USERNAME -Repo terra-climate-extremes
Parameters:
  -GitHubUser (required)
  -Repo (required)
  -Remote (optional, default origin)
  -Force (optional) skip safety prompt if repo already initialized
#>
param(
  [Parameter(Mandatory=$true)][string]$GitHubUser,
  [Parameter(Mandatory=$true)][string]$Repo,
  [string]$Remote='origin',
  [switch]$Force
)

Write-Host "[INFO] Searching for git.exe on drive D: ..."
$candidates = @(
  'D:\Program Files\Git\cmd\git.exe',
  'D:\Git\cmd\git.exe',
  'D:\Git\bin\git.exe',
  'D:\Apps\Git\cmd\git.exe',
  'D:\Apps\Git\bin\git.exe'
)
$found = $null
foreach($c in $candidates){ if(Test-Path $c){ $found = $c; break } }
if(-not $found){
  # broader search fallback (may take time) limited depth
  Write-Host "[INFO] Quick candidates not found; doing fallback scan (depth-limited) ..."
  try {
    $found = Get-ChildItem -Path 'D:\' -Filter git.exe -File -Recurse -ErrorAction SilentlyContinue -Depth 4 | Where-Object { $_.FullName -match 'Git' -and $_.FullName -match 'cmd' } | Select-Object -First 1 -ExpandProperty FullName
  } catch { }
}
if(-not $found){
  Write-Error "git.exe not located on D:. Specify path manually or reinstall Git."
  exit 1
}
Write-Host "[INFO] Found git: $found"
$gitDir = Split-Path $found
if(-not ($env:Path.Split(';') -contains $gitDir)){
  $env:Path = "$gitDir;" + $env:Path
  Write-Host "[INFO] Temporarily added $gitDir to PATH"
}

# Verify
$version = & git --version 2>$null
if(-not $version){ Write-Error "git not executable even after PATH update."; exit 1 }
Write-Host "[INFO] $version"

# Move to project root (assumes script run from inside project or parent)
$projRoot = Split-Path $MyInvocation.MyCommand.Path -Parent | Split-Path -Parent
if(-not (Test-Path (Join-Path $projRoot 'README.md'))){
  Write-Host "[WARN] Could not positively verify project root via README.md; using current $projRoot"
}
Set-Location $projRoot

# Initialize repo
if(-not (Test-Path '.git')){
  git init | Out-Null
  Write-Host "[INFO] Initialized git repository"
} elseif(-not $Force){
  Write-Host "[INFO] .git already exists. Use -Force to proceed anyway."
}

# Add and commit
$hasCommit = git rev-parse --verify HEAD 2>$null
if(-not $hasCommit){
  git add .
  git commit -m "Initial scaffold: Terra Climate Extremes project" | Out-Null
  Write-Host "[INFO] Created initial commit"
} else {
  Write-Host "[INFO] Existing commits detected; staging updates..."
  git add .
  git commit -m "Update" | Out-Null
}

# Set branch
try { git branch -M main | Out-Null } catch { }

# Remote
$remoteUrl = "https://github.com/$GitHubUser/$Repo.git"
$remoteExists = git remote 2>$null | Select-String -SimpleMatch $Remote
if(-not $remoteExists){
  git remote add $Remote $remoteUrl
  Write-Host "[INFO] Added remote $Remote -> $remoteUrl"
} else {
  Write-Host "[INFO] Remote $Remote already exists"
}

# Push
Write-Host "[INFO] Pushing to $remoteUrl ..."
try {
  git push -u $Remote main
  Write-Host "[SUCCESS] Repository pushed to GitHub: $remoteUrl"
} catch {
  Write-Error "Push failed. If authentication error: create a Personal Access Token and retry. $_"
  exit 1
}
