FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg nginx \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY frontend/package*.json /app/frontend/
RUN cd /app/frontend && npm install

COPY app /app/app
COPY frontend /app/frontend
COPY docker/single-nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/start.sh /app/start.sh

RUN cd /app/frontend && npm run build \
    && rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf.bak \
    && chmod +x /app/start.sh \
    && mkdir -p /app/uploads /app/data/db

EXPOSE 80

CMD ["/app/start.sh"]
