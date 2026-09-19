@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo   Shipwright-PTBR - instalacao e inicializacao
echo ================================================
echo.

REM Use %%CD%% instead of %%~dp0 as the argument value.
REM %%~dp0 always ends with a backslash; when passed as the final character
REM inside quotes to powershell.exe it can be parsed with a stray quote on
REM some Windows configurations, producing "Caracteres invalidos no caminho".
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\ptbr_release\setup_release.ps1" -AppDir "%CD%"

set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
    echo.
    echo Falha na preparacao/inicializacao. Codigo: %ERR%
    echo Consulte o README.md e a saida acima.
    pause
    exit /b %ERR%
)

endlocal
