FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    fail2ban \
    iptables \
    iproute2 \
    nginx-extras \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

COPY fail2ban/jail.local /etc/fail2ban/jail.local
COPY fail2ban/filter.d/ /etc/fail2ban/filter.d/

COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx-api.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8001

CMD ["/start.sh"]
