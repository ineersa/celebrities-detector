### Install
App made with python 3.10 and sqlite3

Create new sqlite database in `data` directory:
```bash
sqlite3 celebrities.db
```

Copy `.env` to `.env.local` and change needed variables.

Install dependencies for python:
```bash
apt install python3-pip nginx uwsgi uwsgi-plugin-python3
apt install python3-venv
```

Create venv
```bash
python3 -m venv ./venv
```

Activate venv
```bash
source ./venv/bin/activate
```

Install dependencies
```bash
pip install -r requirements.txt
```

Deactivate venv
```bash
deactivate
```
We will serve application via uwsgi and nginx. 
Create service file for uwsgi:
```bash
touch /etc/systemd/system/app_uwsgi.service

[Unit]
Description=uWSGI instance to serve celebrities app
After=network.target

[Service]
User=username
Group=groupname
WorkingDirectory=/path/to/your/app
Environment="PATH=/path/to/your/virtualenv/bin"
ExecStart=/usr/bin/uwsgi --ini /path/to/your/app/myapp_uwsgi.ini

[Install]
WantedBy=multi-user.target
```

Add service to autostart
```bash
sudo systemctl start app_uwsgi
sudo systemctl enable app_uwsgi
```

Create nginx config file:
```bash
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/path/to/your/app/myapp.sock;
    }

    # ... (additional settings, such as configuring SSL for HTTPS)
}
```
Test and reload nginx
```bash
sudo ln -s /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl reload nginx
```