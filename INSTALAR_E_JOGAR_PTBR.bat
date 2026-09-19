@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo   Shipwright-PTBR - instalacao e inicializacao
echo ================================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\ptbr_release\setup_release.ps1" -AppDir "%~dp0"

set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
    echo.
    echo Falha na preparacao/inicializacao. Codigo: %ERR%
    echo Consulte o README.md e a saida acima.
    pause
    exit /b %ERR%
)

endlocal
