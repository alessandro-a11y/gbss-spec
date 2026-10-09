#!/bin/bash
# Uso: ./kali_heartbeat.sh IP_DA_API IP_DO_KALI CHAVE
API="$1"; MYIP="$2"; KEY="$3"
if [ -z "$API" ] || [ -z "$MYIP" ] || [ -z "$KEY" ]; then
  echo "Uso: $0 IP_DA_API IP_DO_KALI CHAVE"; exit 1
fi
while true; do
  curl -s -o /dev/null -X POST "http://$API:8000/machines/heartbeat" \
    -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
    -d "{\"hostname\":\"KALI\",\"ip\":\"$MYIP\",\"role\":\"attacker\"}"
  sleep 15
done