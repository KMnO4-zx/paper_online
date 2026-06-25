FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /app/frontend-react

COPY frontend-react/package.json frontend-react/package-lock.json ./
RUN npm ci
COPY frontend-react/ ./
RUN npm run build


FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# 安装 Python 生产依赖，保持和本地 uv.lock 一致
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 复制项目文件
COPY ./ /app
COPY --from=frontend-builder /app/frontend-react/dist /app/frontend-react/dist

# 在 backend 目录下启动，端口等配置来自 /app/config.yaml
WORKDIR /app/backend
CMD python /app/scripts/apply_migrations.py && python /app/scripts/run_server.py
