FROM python:3.11-slim
# node24 + dsh CLI（dsh 入口依赖 import.meta.main，需 node>=22；与宿主 24.x 对齐）
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
 && mkdir -p /etc/apt/keyrings \
 && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
 && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_24.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
 && apt-get update && apt-get install -y --no-install-recommends nodejs \
 && npm i -g @deepseek-ai/dsh@0.2.0-rc.2 --no-audit --no-fund \
 && apt-get purge -y curl gnupg && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* \
 && node --version && dsh --version
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY run.py ./
ENV PYTHONUNBUFFERED=1 DSH_BIN=dsh DSH_TIMEOUT_S=180
EXPOSE 5001
CMD ["python", "run.py"]
