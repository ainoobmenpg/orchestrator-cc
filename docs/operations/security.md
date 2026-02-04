# セキュリティ設定

このドキュメントでは、orchestrator-cc のセキュリティ設定について説明します。

---

## 現在のセキュリティ状況

### 実装済みの機能

- なし

### 現在の制約事項

| 項目 | 現状 | リスク |
|------|------|--------|
| **API認証** | なし | 誰でもAPIにアクセス可能 |
| **CORS設定** | 全許可 (`*`) | 任意のオリジンからアクセス可能 |
| **HTTPS対応** | なし | 通信が平文で送信される |
| **シークレット管理** | なし | APIキー等が設定ファイルに含まれる可能性 |

---

## 推奨されるセキュリティ対策

### 1. API 認証

#### JWT トークン認証（推奨）

**提案**: JWT トークンによる API 認証を実装

```python
# orchestrator/web/auth.py
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, Depends, Header

SECRET_KEY = "your-secret-key-change-in-production"  # 環境変数で設定
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    return verify_token(token)
```

**API エンドポイントへの適用**:

```python
from orchestrator.web.auth import get_current_user

@app.get("/api/status")
async def get_status(_user: dict = Depends(get_current_user)):
    return _dashboard_monitor.get_cluster_status()
```

**認証付きリクエストの例**:

```bash
# トークンの取得
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret"}'

# トークンを使用してAPIアクセス
curl http://localhost:8000/api/status \
  -H "Authorization: Bearer <token>"
```

---

#### API キー認証（簡易版）

**提案**: シンプルな API キー認証

```python
# orchestrator/web/auth.py
API_KEY = os.getenv("ORCHESTRATOR_API_KEY", "change-me-in-production")

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

@app.get("/api/status")
async def get_status(_auth: bool = Depends(verify_api_key)):
    return _dashboard_monitor.get_cluster_status()
```

**リクエストの例**:

```bash
curl http://localhost:8000/api/status \
  -H "X-API-Key: your-api-key"
```

---

### 2. HTTPS 対応

#### Let's Encrypt + リバースプロキシ

**提案**: nginx をリバースプロキシとして使用

**nginx 設定例**:

```nginx
# /etc/nginx/sites-available/orchestrator-cc
server {
    listen 80;
    server_name orchestrator.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name orchestrator.example.com;

    ssl_certificate /etc/letsencrypt/live/orchestrator.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/orchestrator.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 対応
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**証明書の取得**:

```bash
# Certbot のインストール
sudo apt-get install certbot python3-certbot-nginx

# 証明書の取得
sudo certbot --nginx -d orchestrator.example.com

# 自動更新の確認
sudo certbot renew --dry-run
```

---

### 3. CORS 設定

**現在の実装**:

```python
# orchestrator/web/dashboard.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 全許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**推奨される設定**:

```python
import os

# 環境変数で許可オリジンを設定
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # 特定のオリジンのみ許可
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # 必要なメソッドのみ
    allow_headers=["Content-Type", "Authorization"],  # 必要なヘッダーのみ
)
```

**環境変数設定**:

```bash
# .env
ALLOWED_ORIGINS=https://dashboard.example.com,https://admin.example.com
```

---

### 4. シークレット管理

#### python-dotenv の使用

**提案**: `.env` ファイルでシークレットを管理

```python
# requirements.txt に追加
python-dotenv>=1.0.0

# orchestrator/web/dashboard.py
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("ORCHESTRATOR_SECRET_KEY")
API_KEY = os.getenv("ORCHESTRATOR_API_KEY")
```

**`.env` ファイル例**:

```bash
# .env
ORCHESTRATOR_SECRET_KEY=your-random-secret-key-here
ORCHESTRATOR_API_KEY=your-api-key-here
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

**`.gitignore` に追加**:

```
.env
.env.local
.env.production
*.key
*.pem
```

---

#### シークレット生成スクリプト

**提案**: シークレット生成用スクリプトを作成

```bash
#!/bin/bash
# scripts/generate-secrets.sh

# シークレットキーの生成
SECRET_KEY=$(openssl rand -hex 32)
API_KEY=$(openssl rand -hex 16)

# .env ファイルの作成
cat > .env << EOF
ORCHESTRATOR_SECRET_KEY=$SECRET_KEY
ORCHESTRATOR_API_KEY=$API_KEY
EOF

echo "Secrets generated in .env"
echo "Make sure to add .env to .gitignore"
```

---

### 5. セキュリティヘッダー

**提案**: セキュリティヘッダーを追加

```python
from fastapi.middleware import Middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

# ミドルウェアの追加
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["orchestrator.example.com"])
```

---

### 6. レート制限

**提案**: API リクエストのレート制限を実装

```python
# orchestrator/web/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/status")
@limiter.limit("10/minute")
async def get_status():
    return _dashboard_monitor.get_cluster_status()
```

---

### 7. ログ監査

**提案**: セキュリティイベントのログ記録

```python
import logging

security_logger = logging.getLogger("security")

@app.middleware("http")
async def log_requests(request, call_next):
    security_logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    security_logger.info(f"Response: {response.status_code}")
    return response
```

---

## セキュリティチェックリスト

### デプロイ前の確認事項

- [ ] SECRET_KEY をデフォルト値から変更している
- [ ] API 認証が有効になっている
- [ ] CORS 設定が適切に設定されている
- [ ] HTTPS が有効になっている（本番環境）
- [ ] シークレットがバージョン管理に含まれていない
- [ ] ファイアウォールが適切に設定されている
- [ ] セキュリティヘッダーが有効になっている
- [ ] レート制限が有効になっている
- [ ] ログ監査が有効になっている

---

## 関連ドキュメント

- [deployment.md](deployment.md) - デプロイ手順
- [configuration.md](configuration.md) - 設定管理
- [troubleshooting.md](troubleshooting.md) - トラブルシューティング
