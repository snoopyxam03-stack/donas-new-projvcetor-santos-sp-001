# Guia de Deploy — Portal de Inscrição Polícia Penal RN (Instituto Avalia)

Este guia cobre a instalação completa em uma VPS Linux (Ubuntu 22.04 recomendado).

---

## 🗂️ Arquitetura

- **Backend** — FastAPI (Python 3.11) na porta interna **8001**
- **Frontend público** — HTML estático servido em `/app/frontend/public/*.html`
- **Painel Admin** — React build compilado em `/app/frontend/public/donaspainel/`
- **Banco** — MongoDB (local ou remoto)

## 📋 Pré-requisitos na VPS

```bash
sudo apt update && sudo apt install -y \
  python3.11 python3.11-venv python3.11-dev python3-pip \
  nodejs npm nginx mongodb-org supervisor git
sudo npm install -g yarn
```

Habilitar serviços:
```bash
sudo systemctl enable --now mongod
sudo systemctl enable --now nginx
sudo systemctl enable --now supervisor
```

---

## 🔧 1) Clonar e configurar

```bash
sudo mkdir -p /var/www && cd /var/www
sudo git clone https://github.com/SEU_USUARIO/SEU_REPO.git portal
sudo chown -R $USER:$USER /var/www/portal
cd /var/www/portal
```

## 🐍 2) Backend

```bash
cd /var/www/portal/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Editar `.env`** (`nano /var/www/portal/backend/.env`):

```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="portal_pprn_prod"
CORS_ORIGINS="https://seudominio.com.br,https://www.seudominio.com.br"
```

⚠️ **CORS_ORIGINS** — coloque APENAS os domínios reais que vão consumir a API. Não deixe `*` em produção.

**Testar backend manualmente:**
```bash
cd /var/www/portal/backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001
```
Abra outra aba SSH e teste: `curl http://localhost:8001/api/pix/qr.png` → deve retornar bytes de imagem PNG.

## ⚛️ 3) Frontend (Painel Admin já vem compilado)

O painel admin JÁ vem compilado em `/app/frontend/public/donaspainel/`. Apenas garantir servir estático.

Se quiser recompilar por qualquer motivo:
```bash
cd /var/www/portal/frontend
yarn install
yarn build   # gera build em ./build → copie para public/donaspainel/
```

**Editar `.env`** (`nano /var/www/portal/frontend/.env`):
```env
REACT_APP_BACKEND_URL=https://seudominio.com.br
```

---

## 🌐 4) Configurar Nginx

Crie `/etc/nginx/sites-available/portal`:

```nginx
server {
    listen 80;
    server_name seudominio.com.br www.seudominio.com.br;

    # Servir HTML/assets estáticos do site público
    root /var/www/portal/frontend/public;
    index inicio.html index.html;

    client_max_body_size 20M;

    # Rotas amigáveis do fluxo público
    location = / { try_files /inicio.html =404; }
    location = /inscricao { try_files /inscricao.html =404; }
    location = /inscricao/contato { try_files /inscricao-contato.html =404; }
    location = /inscricao/endereco { try_files /inscricao-endereco.html =404; }
    location = /inscricao/informacoes { try_files /inscricao-informacoes.html =404; }
    location = /inscricao/confirmacao { try_files /inscricao-confirmacao.html =404; }
    location = /inscricao/pagamento { try_files /inscricao-pagamento.html =404; }
    location = /inscricao/pagamento/pix { try_files /inscricao-pagamento-pix.html =404; }

    # Painel administrativo (React SPA)
    location /donaspainel {
        alias /var/www/portal/frontend/public/donaspainel;
        try_files $uri $uri/ /donaspainel/index.html;
    }
    location /farpapainel {
        alias /var/www/portal/frontend/public/donaspainel;
        try_files $uri $uri/ /donaspainel/index.html;
    }
    # Downloader de documentos
    location = /donaspainel/documentos {
        try_files /donaspainel-documentos.html =404;
    }

    # API proxy → FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # Assets estáticos gerais
    location / {
        try_files $uri $uri/ =404;
    }
}
```

Ativar:
```bash
sudo ln -sf /etc/nginx/sites-available/portal /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default   # (opcional)
sudo nginx -t && sudo systemctl reload nginx
```

## 🔐 5) HTTPS (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d seudominio.com.br -d www.seudominio.com.br
sudo systemctl enable --now certbot.timer
```

---

## 🤖 6) Rodar o backend com Supervisor

Crie `/etc/supervisor/conf.d/portal-backend.conf`:

```ini
[program:portal-backend]
command=/var/www/portal/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
directory=/var/www/portal/backend
autostart=true
autorestart=true
stdout_logfile=/var/log/portal-backend.out.log
stderr_logfile=/var/log/portal-backend.err.log
environment=PYTHONUNBUFFERED="1"
user=www-data
```

```bash
sudo mkdir -p /var/log && sudo chown -R www-data /var/www/portal
sudo supervisorctl reread && sudo supervisorctl update
sudo supervisorctl start portal-backend
sudo supervisorctl status portal-backend
```

---

## 🌱 7) Seed inicial (Admin + Config PIX + Telegram)

Após backend rodar pela primeira vez, criar o admin e cadastrar chave PIX/Telegram:

```bash
# Terminal na VPS
cd /var/www/portal/backend
source venv/bin/activate
python3 -c "
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from dotenv import load_dotenv
load_dotenv('.env')
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def seed():
    c = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = c[os.environ['DB_NAME']]
    # Admin (USUÁRIO/SENHA — TROQUE!)
    await db.admins.update_one(
        {'username':'farpa'},
        {'\$set':{'username':'farpa','password_hash':pwd.hash('Ads102030'),'role':'admin'}},
        upsert=True
    )
    # Configurações PIX e Telegram (EDITE COM SEUS DADOS)
    await db.settings.update_one(
        {'_id':'main'},
        {'\$set': {
            'pix_key':'sua-chave-pix@aqui.com',
            'pix_nome':'INSTITUTO AVALIA',
            'pix_cidade':'NATAL',
            'telegram_enabled': True,
            'telegram_bot_token':'SEU_BOT_TOKEN_AQUI',
            'telegram_chat_id':'SEU_CHAT_ID_AQUI',
            'telegram_titulo':'Portal PPRN',
        }},
        upsert=True
    )
    print('Admin criado: farpa / Ads102030 (TROQUE A SENHA)')
    print('Settings PIX + Telegram inseridos')
asyncio.run(seed())
"
```

## ⚠️ Segurança em produção

- [ ] Trocar senha do admin `farpa/Ads102030` para uma senha forte
- [ ] Configurar `CORS_ORIGINS` com o domínio real (não `*`)
- [ ] MongoDB com autenticação (crie usuário e senha em `MONGO_URL`)
- [ ] Renovar certificado HTTPS automaticamente (certbot já faz)
- [ ] Backups periódicos do MongoDB: `mongodump --db portal_pprn_prod --out /backup/`
- [ ] Firewall UFW: `sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable`

## 🧪 Verificação final

- `https://seudominio.com.br/` → home pública com brasão + botão inscrição
- `https://seudominio.com.br/inscricao` → formulário
- `https://seudominio.com.br/farpapainel` → login admin (`farpa` / sua nova senha)
- `https://seudominio.com.br/api/pix/qr.png` → imagem PNG do QR PIX

## 🐞 Troubleshooting

**Backend não sobe?**
```bash
sudo tail -f /var/log/portal-backend.err.log
```

**MongoDB conexão negada?**
```bash
sudo systemctl status mongod
mongosh --eval "db.runCommand({ping:1})"
```

**Frontend público 404?** Verifique se os `.html` estão em `/var/www/portal/frontend/public/`.

**Painel admin em branco?** O `.env` do frontend precisa apontar para a URL pública correta (`REACT_APP_BACKEND_URL`).

**Erro "413 Request Entity Too Large" ao anexar documentos?**
Adicione no `nginx.conf` server block: `client_max_body_size 20M;` (já incluído neste guia).

---

## 📞 Suporte

- Backend: FastAPI + Motor (async MongoDB)
- Frontend público: HTML estático vanilla (sem build)
- Painel admin: React CRA (já compilado)
- PIX: geração local (EMV BACEN) via `qrcode` lib
- Telegram: notificações via Bot API oficial

Boa sorte com o deploy! 🍺
