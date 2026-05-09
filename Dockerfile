# 多阶段构建
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml README.md ./

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir build

# 构建wheel
COPY src/ ./src/
RUN python -m build

# 生产镜像
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -u 1000 fundcli

# 复制构建产物
COPY --from=builder /app/dist/*.whl /tmp/

# 安装应用
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm /tmp/*.whl

# 创建缓存目录
RUN mkdir -p /home/fundcli/.fund_cli/cache && \
    chown -R fundcli:fundcli /home/fundcli

USER fundcli

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV FUND_CLI_HOME=/home/fundcli/.fund_cli

# 验证安装
RUN fund --version

ENTRYPOINT ["fund"]
CMD ["--help"]
