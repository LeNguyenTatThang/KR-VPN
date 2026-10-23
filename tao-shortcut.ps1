# Tao shortcut "KR VPN" tren Desktop tro toi thu muc cua app
$dir  = $PSScriptRoot
$desk = [Environment]::GetFolderPath('Desktop')
$ws   = New-Object -ComObject WScript.Shell
$lnk  = $ws.CreateShortcut((Join-Path $desk 'KR VPN.lnk'))
$lnk.TargetPath       = Join-Path $dir 'KR-VPN.bat'
$lnk.WorkingDirectory = $dir
$lnk.IconLocation     = Join-Path $dir 'kr.ico'
$lnk.Description      = 'KR VPN - IP Han Quoc'
$lnk.WindowStyle      = 7
$lnk.Save()
Write-Host "Da tao shortcut: $(Join-Path $desk 'KR VPN.lnk')"
Write-Host "Tro toi: $dir\KR-VPN.bat"
