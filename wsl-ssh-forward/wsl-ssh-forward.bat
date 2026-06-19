@echo off
setlocal enabledelayedexpansion

:: Auto-forward SSH from Windows port 2222 to WSL2
:: WSL2 IP changes on every reboot — this script auto-detects it

:: Ambil IP WSL
for /f "tokens=2 delims= " %%a in ('wsl -- ip addr show eth0 ^| findstr /c:"inet " ^| findstr /v "inet6"') do (
    for /f "tokens=1 delims=/" %%b in ("%%a") do set WSL_IP=%%b
)

echo WSL IP: %WSL_IP%
if "%WSL_IP%"=="" (
    echo ERROR: Gagal dapat IP WSL. Pastikan WSL sudah running.
    exit /b 1
)

:: Hapus rule lama kalo ada (abaikan error kalo belum ada)
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=2222 >nul 2>&1

:: Tambah rule baru
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=2222 connectaddress=%WSL_IP% connectport=22
if %errorlevel% equ 0 (
    echo Port forwarding: 0.0.0.0:2222 -^> %WSL_IP%:22
) else (
    echo ERROR: Gagal menambah port forwarding.
    exit /b 1
)

:: Pastikan firewall rule ada
netsh advfirewall firewall add rule name="SSH WSL 2222" dir=in action=allow protocol=TCP localport=2222 >nul 2>&1

:: Verifikasi
echo.
echo Active portproxy rules:
netsh interface portproxy show all

endlocal
