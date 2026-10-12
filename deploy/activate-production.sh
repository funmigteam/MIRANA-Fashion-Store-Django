#!/usr/bin/env bash
set -euo pipefail

project_dir='/srv/mirana_poosh'
cd "$project_dir"

if [ "$(id -un)" != 'deploy' ]; then
    echo 'Run this script as deploy, not root.' >&2
    exit 1
fi

./.venv-production/bin/python manage.py migrate --noinput
MIRANA_DEBUG=0 \
MIRANA_SECRET_KEY='validation-only-not-used-in-production' \
MIRANA_ALLOWED_HOSTS='miranastyle.ir,www.miranastyle.ir' \
MIRANA_CSRF_ORIGINS='https://miranastyle.ir,https://www.miranastyle.ir' \
./.venv-production/bin/python manage.py collectstatic --noinput

secret=$(openssl rand -hex 48)
sudo install -d -m 0750 -o root -g deploy /etc/mirana
printf '%s\n' \
  'MIRANA_DEBUG=0' \
  "MIRANA_SECRET_KEY=$secret" \
  'MIRANA_ALLOWED_HOSTS=miranastyle.ir,www.miranastyle.ir' \
  'MIRANA_CSRF_ORIGINS=https://miranastyle.ir,https://www.miranastyle.ir' \
  'MIRANA_SECURE_SSL_REDIRECT=1' | sudo tee /etc/mirana/production.env >/dev/null
sudo chown root:deploy /etc/mirana/production.env
sudo chmod 0640 /etc/mirana/production.env

sudo install -m 0644 deploy/mirana.service /etc/systemd/system/mirana.service
sudo install -m 0644 deploy/mirana.nginx.conf /etc/nginx/sites-available/mirana.conf
sudo ln -sfn /etc/nginx/sites-available/mirana.conf /etc/nginx/sites-enabled/mirana.conf
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now mirana.service
sudo systemctl reload nginx

systemctl --no-pager --full status mirana.service
curl --fail --silent --show-error -H 'Host: miranastyle.ir' http://127.0.0.1/
echo
echo 'Mirana is active on the origin. Finish Arvan DNS/proxy configuration, then verify https://miranastyle.ir.'
