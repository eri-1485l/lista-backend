#!/bin/bash
set -e

mkdir -p /var/log
touch /var/log/backend-access.log

# Rate limiting en el puerto 8001 (el que expone Nginx)
iptables -A INPUT -p tcp --dport 8001 -m conntrack --ctstate NEW \
    -m recent --set --name HTTPFLOOD_BACKEND
iptables -A INPUT -p tcp --dport 8001 -m conntrack --ctstate NEW \
    -m recent --update --seconds 60 --hitcount 600 --name HTTPFLOOD_BACKEND -j DROP

fail2ban-client -x start

# Uvicorn en el puerto interno 8002 (no accesible desde fuera)
uvicorn app.main:app --host 127.0.0.1 --port 8002 --access-log 2>&1 | tee -a /var/log/backend-access.log &

sleep 2

# Nginx en primer plano
exec nginx -g "daemon off;"
