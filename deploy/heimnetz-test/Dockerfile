# SPDX-License-Identifier: GPL-3.0-or-later
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/bienenlogger
RUN groupadd --system bienenlogger && useradd --system --no-create-home --gid bienenlogger bienenlogger \
    && pip install --no-cache-dir 'fastapi>=0.115,<1' 'uvicorn>=0.30,<1' 'psycopg[binary]>=3.2,<4' 'argon2-cffi>=23,<26'
COPY server/datenbank/*.py /srv/bienenlogger/server/datenbank/
COPY prototype/claude-ui/index.html prototype/claude-ui/app.js prototype/claude-ui/style.css \
     prototype/claude-ui/stockkarte_native.js prototype/claude-ui/stockkarte_live.js \
     prototype/claude-ui/stockkarte_edit.js /srv/bienenlogger/prototype/claude-ui/
USER bienenlogger
EXPOSE 8765
CMD ["uvicorn", "stockkarte_dev_web:app", "--app-dir", "/srv/bienenlogger/server/datenbank", \
     "--host", "0.0.0.0", "--port", "8765", "--no-access-log", \
     "--no-proxy-headers"]
