#!/usr/bin/env bash
#
# WOSZ starten — dubbelklik op dit bestand.
#
# Dit script doet alles wat nodig is: het installeert wat ontbreekt, zet de
# database klaar, start de server en het dashboard, en opent je browser.
# De eerste keer duurt het een paar minuten; daarna gaat het snel.
#
# Stoppen: sluit dit venster, of druk op Ctrl+C.

set -u

# Ga naar de map waar dit bestand staat, waar je het ook vandaan start.
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1

BACKEND_POORT=8000
DASHBOARD_POORT=8090

echo ""
echo "=============================================="
echo "  WOSZ — AI-organisatie"
echo "=============================================="
echo ""

# --- 1. uv ------------------------------------------------------------------
# uv is het hulpprogramma dat de rest installeert. Eén keer nodig.

if ! command -v uv > /dev/null 2>&1; then
    # Misschien staat het er al, maar kent de terminal het pad nog niet.
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! command -v uv > /dev/null 2>&1; then
    echo "[1/5] Hulpprogramma 'uv' installeren (eenmalig)..."
    if ! curl -LsSf https://astral.sh/uv/install.sh | sh > /dev/null 2>&1; then
        echo ""
        echo "  Dat lukte niet. Meestal is er dan geen internetverbinding."
        echo "  Probeer het opnieuw, of installeer uv handmatig via:"
        echo "  https://docs.astral.sh/uv/getting-started/installation/"
        echo ""
        read -r -p "Druk op Enter om te sluiten."
        exit 1
    fi
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    echo "      Klaar."
else
    echo "[1/5] Hulpprogramma 'uv' is al aanwezig."
fi

cd backend || { echo "Kan de map 'backend' niet vinden."; read -r; exit 1; }

# --- 2. Python-omgeving -----------------------------------------------------

if [ ! -d .venv ]; then
    echo "[2/5] Python-omgeving aanmaken (eenmalig, kan even duren)..."
    uv venv --python 3.11 .venv > /dev/null 2>&1 || {
        echo "  Dat lukte niet. Draai dit script opnieuw of vraag om hulp."
        read -r -p "Druk op Enter om te sluiten."
        exit 1
    }
else
    echo "[2/5] Python-omgeving staat al klaar."
fi

PY=".venv/bin/python"
[ -x "$PY" ] || PY=".venv/Scripts/python.exe"   # Windows via Git Bash

echo "[3/5] Benodigde onderdelen installeren..."
uv pip install --python "$PY" -q -e . || {
    echo "  Installeren mislukte. Controleer je internetverbinding."
    read -r -p "Druk op Enter om te sluiten."
    exit 1
}

# --- 3. Instellingen en database --------------------------------------------

if [ ! -f .env ]; then
    cp .env.example .env
    echo "      Instellingenbestand aangemaakt (.env)."
fi

if [ ! -f wosz.db ]; then
    echo "[4/5] Database vullen met voorbeeldgegevens..."
    "$PY" -m app.db.seed
    # Laat de agents meteen één ronde draaien, anders staat het dashboard
    # de eerste keer op nul en lijkt het alsof er niets werkt.
    "$PY" -m app.db.demo
else
    echo "[4/5] Database staat al klaar."
fi

# --- 4. Servers starten -----------------------------------------------------

# Draait er al iets op deze poorten? Dan is WOSZ waarschijnlijk al gestart in
# een ander venster. Zonder deze controle krijg je een onbegrijpelijke
# foutmelding over "address already in use".
# Probeert de poort te claimen. Lukt dat, dan is hij vrij. Dit is betrouwbaarder
# dan een testverbinding: wie een netwerkproxy heeft ingesteld, krijgt daarop
# een antwoord van de proxy en zou denken dat elke poort bezet is.
poort_bezet() {
    ! "$PY" - "$1" <<'PYEOF' > /dev/null 2>&1
import socket, sys
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    s.bind(("127.0.0.1", int(sys.argv[1])))
finally:
    s.close()
PYEOF
}

for poort in "$BACKEND_POORT" "$DASHBOARD_POORT"; do
    if poort_bezet "$poort"; then
        echo ""
        echo "  Er draait al iets op poort $poort."
        echo ""
        echo "  Waarschijnlijk staat WOSZ al aan in een ander venster."
        echo "  Kijk of je hem al open hebt staan op:"
        echo "  http://localhost:$DASHBOARD_POORT/wosz-app.html"
        echo ""
        echo "  Zo niet: sluit het andere venster en probeer het opnieuw."
        echo ""
        read -r -p "Druk op Enter om te sluiten."
        exit 1
    fi
done

echo "[5/5] Starten..."

"$PY" -m uvicorn app.main:app --port "$BACKEND_POORT" --log-level warning &
BACKEND_PID=$!

(cd ../frontend && "../backend/$PY" -m http.server "$DASHBOARD_POORT" > /dev/null 2>&1) &
DASHBOARD_PID=$!

# Netjes afsluiten als het venster dichtgaat of je Ctrl+C drukt.
opruimen() {
    echo ""
    echo "WOSZ wordt gestopt..."
    kill "$BACKEND_PID" "$DASHBOARD_PID" 2>/dev/null
    wait "$BACKEND_PID" "$DASHBOARD_PID" 2>/dev/null
    echo "Gestopt."
}
trap opruimen EXIT INT TERM

# Wachten tot de server echt luistert.
for _ in $(seq 1 30); do
    if curl -s "http://localhost:$BACKEND_POORT/health" > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

DASHBOARD_URL="http://localhost:$DASHBOARD_POORT/wosz-app.html"

echo ""
echo "=============================================="
echo "  WOSZ draait."
echo ""
echo "  Dashboard:  $DASHBOARD_URL"
echo "  Knoppen:    http://localhost:$BACKEND_POORT/docs"
echo ""
echo "  Log in met de knop 'Demo: directie'."
echo "  Stoppen: sluit dit venster of druk op Ctrl+C."
echo "=============================================="
echo ""

# Browser openen (macOS, Linux, Windows via Git Bash).
if command -v open > /dev/null 2>&1; then
    open "$DASHBOARD_URL"
elif command -v xdg-open > /dev/null 2>&1; then
    xdg-open "$DASHBOARD_URL" > /dev/null 2>&1
elif command -v start > /dev/null 2>&1; then
    start "$DASHBOARD_URL"
fi

wait "$BACKEND_PID"
