#!/bin/sh
set -e

cd /app

# 启动后端
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# 启动前端开发服务器
cd /app/frontend
npm run dev -- --host 0.0.0.0 --port 5173 &

# 前台启动 Nginx
nginx -g 'daemon off;'
