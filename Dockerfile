FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /app/frontend-react

COPY frontend-react/package.json frontend-react/package-lock.json ./
RUN npm ci
COPY frontend-react/ ./
RUN npm run build


FROM python:3.10-slim

WORKDIR /app

# 复制项目文件
COPY ./ /app
COPY --from=frontend-builder /app/frontend-react/dist /app/frontend-react/dist

# 安装依赖
RUN pip install --no-cache-dir fastapi uvicorn openai python-dotenv requests sse-starlette supabase tiktoken

# 在 backend 目录下启动，使用 $PORT 环境变量
WORKDIR /app/backend
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
