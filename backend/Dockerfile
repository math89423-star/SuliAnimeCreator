FROM python:3.11-slim
# 国内源：apt（debian官方/node源太慢，换清华；nodesource key仍走官方，只一次）+ pip（清华）
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
# node24 运行时（dsh 入口依赖 import.meta.main，需 node>=22；与宿主 24.x 对齐）+ ffmpeg（视频抽帧/转码，video-frames 工具用）
# dsh CLI 本身**不进镜像**：装在宿主 dsh-runtime/<版本>/ 目录，容器挂载使用。
# 原因：dsh 升版要重装 600+ 包，钉在镜像里等于每次升版都重建整个后端镜像；
# 移出后升版 = 宿主装一次 + 改 DSH_VERSION + 重启容器（见 scripts/dsh-runtime.sh）。
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list /etc/apt/sources.list.d/* 2>/dev/null; \
 apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gnupg ffmpeg \
 && mkdir -p /etc/apt/keyrings \
 && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
 && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_24.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
 && apt-get update && apt-get install -y --no-install-recommends nodejs \
 && apt-get purge -y curl gnupg && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* \
 && node --version
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY run.py ./
ENV PYTHONUNBUFFERED=1 DSH_TIMEOUT_S=180
EXPOSE 5001
CMD ["python", "run.py"]

# ── CA 信任库 ───────────────────────────────────────────────
# eMudhra 中间 CA 被攻破 → 移除 emSign ECC Root CA - G3 与
# Comodo AAA Services root。镜像层会缓存，重建时 --pull（基础镜像 digest 变了）或 --no-cache
# 才会重跑这层；平时改 CA_REFRESH 的值也能强制刷新。
ARG CA_REFRESH=2
RUN echo "ca-refresh=$CA_REFRESH" \
 && apt-get update \
 && apt-get install -y --only-upgrade ca-certificates \
 && rm -rf /var/lib/apt/lists/*
