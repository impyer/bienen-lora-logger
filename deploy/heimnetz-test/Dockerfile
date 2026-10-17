# SPDX-License-Identifier: GPL-3.0-or-later
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/srv/bienenlogger/server/datenbank
WORKDIR /srv/bienenlogger
COPY server/datenbank/requirements.lock /srv/bienenlogger/requirements.lock
RUN groupadd --system bienenlogger && useradd --system --no-create-home --gid bienenlogger bienenlogger \
    && pip install --no-cache-dir -r /srv/bienenlogger/requirements.lock
COPY --chown=bienenlogger:bienenlogger server/datenbank/*.py /srv/bienenlogger/server/datenbank/
COPY --chown=bienenlogger:bienenlogger server/datenbank/umwelt /srv/bienenlogger/server/datenbank/umwelt
COPY --chown=bienenlogger:bienenlogger server/datenbank/migrations /srv/bienenlogger/server/datenbank/migrations
COPY --chown=bienenlogger:bienenlogger prototype/claude-ui/index.html prototype/claude-ui/app.js prototype/claude-ui/style.css \
     prototype/claude-ui/stockkarte_native.js prototype/claude-ui/stockkarte_live.js \
     prototype/claude-ui/stockkarte_edit.js prototype/claude-ui/umwelt.js /srv/bienenlogger/prototype/claude-ui/
COPY --chown=bienenlogger:bienenlogger prototype/claude-ui/vendor /srv/bienenlogger/prototype/claude-ui/vendor
USER bienenlogger
EXPOSE 8765
CMD ["uvicorn", "stockkarte_dev_web:app", "--app-dir", "/srv/bienenlogger/server/datenbank", \
     "--host", "0.0.0.0", "--port", "8765", "--no-access-log", \
     "--no-proxy-headers"]
