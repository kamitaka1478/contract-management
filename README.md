# 契約管理システム

契約情報と請求情報の突合・管理を行うWebアプリケーションシステムです。

## システム概要

### 主な機能
- **契約情報管理**: 契約者情報、契約期間、金額等の一元管理
- **請求情報管理**: 請求書データの登録・管理
- **自動突合機能**: 契約情報と請求情報の自動照合とアラート
- **検索・閲覧機能**: 効率的な情報検索とデータ閲覧
- **CSVインポート**: 既存データの一括取り込み

### 技術スタック
- **フロントエンド**: React 18 + TypeScript + Tailwind CSS
- **バックエンド**: Django 4.2 + Django REST Framework
- **データベース**: PostgreSQL 15
- **インフラ**: AWS VPC (EC2 + RDS)
- **認証**: Django標準認証 + JWT
- **デプロイ**: Docker + GitHub Actions

## システム要件

### 開発環境
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose

### 本番環境
- AWS EC2 (t3.medium以上推奨)
- AWS RDS PostgreSQL
- AWS VPC with Private Subnet
- SSL/TLS証明書

## プロジェクト構成

```
contract-management/
├── frontend/                 # React アプリケーション
│   ├── public/
│   ├── src/
│   │   ├── components/       # 再利用可能コンポーネント
│   │   ├── pages/           # ページコンポーネント
│   │   ├── hooks/           # カスタムフック
│   │   ├── services/        # API通信
│   │   ├── types/           # TypeScript型定義
│   │   └── utils/           # ユーティリティ関数
│   ├── package.json
│   └── tailwind.config.js
├── backend/                  # Django アプリケーション
│   ├── config/              # Django設定
│   ├── apps/
│   │   ├── contracts/       # 契約管理アプリ
│   │   ├── billing/         # 請求管理アプリ
│   │   ├── matching/        # 突合機能アプリ
│   │   └── authentication/ # 認証アプリ
│   ├── requirements.txt
│   └── manage.py
├── infrastructure/           # インフラ設定
│   ├── docker/
│   │   ├── Dockerfile.frontend
│   │   ├── Dockerfile.backend
│   │   └── docker-compose.yml
│   ├── aws/
│   │   ├── terraform/       # Terraform設定
│   │   └── cloudformation/  # CloudFormation設定
│   └── nginx/
├── docs/                    # ドキュメント
│   ├── api/                 # API仕様書
│   ├── architecture/        # アーキテクチャ図
│   └── deployment/          # デプロイ手順
├── README.md
└── .env.example
```

## セットアップ手順

### 1. リポジトリクローン
```bash
git clone <repository-url>
cd contract-management
```

### 2. 環境変数設定
```bash
cp .env.example .env
# .envファイルを編集して適切な値を設定
```

### 3. Docker環境での起動
```bash
# Docker Composeでサービス起動
docker-compose up -d

# データベースマイグレーション
docker-compose exec backend python manage.py migrate

# スーパーユーザー作成
docker-compose exec backend python manage.py `createsuperuser`

# フロントエンド依存関係インストール
docker-compose exec frontend npm install
```

### 4. 開発サーバー起動
```bash
# バックエンド (http://localhost:8000)
docker-compose exec backend python manage.py `runserver` 0.0.0.0:8000

# フロントエンド (http://localhost:3000)
docker-compose exec frontend npm start
```

## API エンドポイント

### 認証
- `POST /api/auth/login/` - ログイン
- `POST /api/auth/logout/` - ログアウト
- `POST /api/auth/refresh/` - トークンリフレッシュ

### 契約管理
- `GET /api/contracts/` - 契約一覧取得
- `POST /api/contracts/` - 契約新規作成
- `GET /api/contracts/{id}/` - 契約詳細取得
- `PUT /api/contracts/{id}/` - 契約更新
- `DELETE /api/contracts/{id}/` - 契約削除
- `POST /api/contracts/import/` - CSV一括インポート

### 請求管理
- `GET /api/billing/` - 請求一覧取得
- `POST /api/billing/` - 請求新規作成
- `GET /api/billing/{id}/` - 請求詳細取得
- `PUT /api/billing/{id}/` - 請求更新
- `DELETE /api/billing/{id}/` - 請求削除

### 突合機能
- `POST /api/matching/run/` - 突合処理実行
- `GET /api/matching/results/` - 突合結果取得
- `GET /api/matching/alerts/` - アラート一覧取得

## データベース設計

### 主要テーブル
- **contracts**: 契約情報
- **billing_records**: 請求情報
- **matching_results**: 突合結果
- **alerts**: アラート情報
- **users**: ユーザー情報

## セキュリティ設定

### 開発環境
- CORS設定でフロントエンドからのアクセスを許可
- JWT認証でAPI保護
- HTTPS強制（本番環境）

### 本番環境
- VPC Private Subnetでデータベース保護
- Security Group で最小限のポート開放
- WAF設定でWebアプリケーション保護
- SSL/TLS暗号化
- 定期的なセキュリティパッチ適用

## デプロイ手順

### AWS環境準備
1. VPC・サブネット作成
2. Security Group設定
3. EC2インスタンス起動
4. RDS PostgreSQL作成
5. SSL証明書設定

### アプリケーションデプロイ
```bash
# Docker イメージビルド
docker build -t contract-frontend ./frontend
docker build -t contract-backend ./backend

# AWS ECR へプッシュ
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com
docker tag contract-frontend:latest <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/contract-frontend:latest
docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/contract-frontend:latest

# EC2 インスタンスでデプロイ
ssh -i `keypair`.pem ec2-user@<ec2-ip>
docker pull <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/contract-frontend:latest
docker-compose -f docker-compose.prod.yml up -d
```

## 監視・ログ

### CloudWatch設定
- アプリケーションログ収集
- システムメトリクス監視
- アラート設定

### ログ管理
- Django: `logs/django.log`
- Nginx: `logs/access.log`, `logs/error.log`
- PostgreSQL: AWS RDS ログ

## トラブルシューティング

### よくある問題
1. **データベース接続エラー**
   - PostgreSQL サービス起動確認
   - 接続設定確認（host, port, user, password）

2. **CORS エラー**
   - Django settings の CORS_ALLOWED_ORIGINS 確認
   - フロントエンドのAPIベースURL確認

3. **認証エラー**
   - JWT トークン有効期限確認
   - ユーザー権限設定確認

## 開発ガイドライン

### コードスタイル
- **Python**: Black + flake8
- **TypeScript**: ESLint + Prettier
- **Git**: Conventional Commits

### テスト
```bash
# バックエンドテスト
docker-compose exec backend python manage.py test

# フロントエンドテスト
docker-compose exec frontend npm test
```

## ライセンス

MIT Licenses