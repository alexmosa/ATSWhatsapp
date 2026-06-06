#!/usr/bin/env bash
# Simula un mensaje entrante de WhatsApp (como lo envía Twilio) sin necesitar Twilio.
# Uso: ./scripts/test_whatsapp.sh "+525511112222" "Hola, ¿qué vacantes tienen?"

set -euo pipefail

PHONE="${1:-+525511112222}"
MESSAGE="${2:-Hola, ¿qué vacantes tienen disponibles?}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo ">> Simulando WhatsApp de $PHONE"
echo ">> Mensaje: $MESSAGE"
echo ""

curl -s -X POST "$BASE_URL/webhooks/whatsapp" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "From=whatsapp:$PHONE" \
  --data-urlencode "To=whatsapp:+14155238886" \
  --data-urlencode "Body=$MESSAGE" \
  --data-urlencode "MessageSid=SM_test_$(date +%s)" \
  --data-urlencode "ProfileName=Candidato Test" \
  | sed 's/<Message>//;s/<\/Message>//;s/<Response>//;s/<\/Response>//;s/&amp;/\&/g;s/&lt;/</g;s/&gt;/>/g;s/&quot;/"/g;s/&apos;/'"'"'/g'

echo ""
