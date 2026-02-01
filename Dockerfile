FROM modelscope-registry.cn-beijing.cr.aliyuncs.com/modelscope-repo/python:3.10

WORKDIR /home/user/app

# 复制项目文件
COPY ./ /home/user/app

# 安装依赖
RUN pip install fastapi uvicorn openai python-dotenv requests sse-starlette

# 魔搭使用 7860 端口
EXPOSE 7860

# 在 backend 目录下启动
WORKDIR /home/user/app/backend
ENTRYPOINT ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
