#!/bin/sh
set -e

cd /app

# 仅启动后端（前端由 Nginx 直接提供构建后的静态文件）
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 前台启动 Nginx
nginx -g 'daemon off;'
