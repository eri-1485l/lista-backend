#!/bin/bash
set -e

mkdir -p /var/log
touch /var/log/backend-access.log

# Rate limiting: máximo 100 conexiones nuevas por minuto al puerto 8001
iptables -A INPUT -p tcp --dport 8001 -m conntrack --ctstate NEW \
    -m recent --set --name HTTPFLOOD_BACKEND
iptables -A INPUT -p tcp --dport 8001 -m conntrack --ctstate NEW \
    -m recent --update --seconds 60 --hitcount 600 --name HTTPFLOOD_BACKEND -j DROP

fail2ban-client -x start

exec uvicorn app.main:app --host 0.0.0.0 --port 8001 --access-log 2>&1 | tee -a /var/log/backend-access.log