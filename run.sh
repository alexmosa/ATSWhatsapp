#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo ">> Creando entorno virtual..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo ">> Instalando dependencias..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
  echo ">> Creando .env desde .env.example..."
  cp .env.example .env
fi

mkdir -p data

echo ">> Cargando datos de demostración..."
python scripts/seed_data.py

echo ""
echo "=========================================="
echo "  ATS WhatsApp — Servidor iniciando"
echo "=========================================="
echo "  URL:      http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Reporte:  http://localhost:8000/api/ats/positions/POS-SEC-003/finalists-report"
echo "=========================================="
echo ""

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
