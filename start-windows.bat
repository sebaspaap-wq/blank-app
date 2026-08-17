@echo off
REM ---------------------------------------------------------------------------
REM  WOSZ starten op Windows — dubbelklik op dit bestand.
REM
REM  Dit script installeert wat ontbreekt, zet de database klaar, start de
REM  server en het dashboard, en opent je browser. De eerste keer duurt het een
REM  paar minuten; daarna gaat het snel.
REM
REM  Stoppen: sluit dit venster.
REM ---------------------------------------------------------------------------

setlocal
cd /d "%~dp0"

set BACKEND_POORT=8000
set DASHBOARD_POORT=8090

echo.
echo ==============================================
echo   WOSZ - AI-organisatie
echo ==============================================
echo.

REM --- 1. uv -----------------------------------------------------------------
where uv >nul 2>&1
if errorlevel 1 (
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

where uv >nul 2>&1
if errorlevel 1 (
    echo [1/5] Hulpprogramma 'uv' installeren ^(eenmalig^)...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" >nul 2>&1
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
    where uv >nul 2>&1
    if errorlevel 1 (
        echo.
        echo   Dat lukte niet. Meestal is er dan geen internetverbinding.
        echo   Installeer uv anders handmatig via:
        echo   https://docs.astral.sh/uv/getting-started/installation/
        echo.
        pause
        exit /b 1
    )
    echo       Klaar.
) else (
    echo [1/5] Hulpprogramma 'uv' is al aanwezig.
)

cd backend
if errorlevel 1 (
    echo Kan de map 'backend' niet vinden.
    pause
    exit /b 1
)

REM --- 2. Python-omgeving ----------------------------------------------------
if not exist ".venv" (
    echo [2/5] Python-omgeving aanmaken ^(eenmalig, kan even duren^)...
    uv venv --python 3.11 .venv >nul 2>&1
    if errorlevel 1 (
        echo   Dat lukte niet. Draai dit script opnieuw of vraag om hulp.
        pause
        exit /b 1
    )
) else (
    echo [2/5] Python-omgeving staat al klaar.
)

set PY=.venv\Scripts\python.exe

echo [3/5] Benodigde onderdelen installeren...
uv pip install --python "%PY%" -q -e .
if errorlevel 1 (
    echo   Installeren mislukte. Controleer je internetverbinding.
    pause
    exit /b 1
)

REM --- 3. Instellingen en database -------------------------------------------
if not exist ".env" (
    copy .env.example .env >nul
    echo       Instellingenbestand aangemaakt ^(.env^).
)

if not exist "wosz.db" (
    echo [4/5] Database vullen met voorbeeldgegevens...
    "%PY%" -m app.db.seed
    REM Laat de agents meteen een ronde draaien, anders staat het dashboard
    REM de eerste keer op nul en lijkt het alsof er niets werkt.
    "%PY%" -m app.db.demo
) else (
    echo [4/5] Database staat al klaar.
)

REM --- 4. Servers starten ----------------------------------------------------
echo [5/5] Starten...

start "WOSZ dashboard" /min cmd /c "cd ..\frontend && ..\backend\%PY% -m http.server %DASHBOARD_POORT%"

echo.
echo ==============================================
echo   WOSZ draait.
echo.
echo   Dashboard:  http://localhost:%DASHBOARD_POORT%/wosz-app.html
echo   Knoppen:    http://localhost:%BACKEND_POORT%/docs
echo.
echo   Log in met de knop 'Demo: directie'.
echo   Stoppen: sluit dit venster.
echo ==============================================
echo.

timeout /t 3 /nobreak >nul
start "" "http://localhost:%DASHBOARD_POORT%/wosz-app.html"

"%PY%" -m uvicorn app.main:app --port %BACKEND_POORT% --log-level warning

endlocal
