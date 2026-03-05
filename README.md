# Invoice Compliance API

請求データを登録し、AIとルールで監査観点のフラグを返す経理オペレーション向けバックエンドです。

## 30秒で伝わる要点

- 何を解くか: 請求レビューの見落としと、属人的な判断基準を減らす。
- 何を実装したか: 請求データの型検証、ルール判定、AI補助コメント、レビュー結果保存を実装した。
- 学生としての強み: AIを「最終判断」ではなく「説明補助」に置き、実務の説明責任を意識している。

## 面接での60秒説明テンプレ

1. 課題: 請求チェックが人依存で、優先レビュー対象の抽出に時間がかかる。  
2. 設計: 金額や明細は厳密型、判定はルールとAI補助を分離して責務を明確化した。  
3. 技術選択: FastAPI + SQLAlchemy で可読性を保ち、監査しやすい出力構造を定義した。  
4. 成果: 説明可能性を保ちつつ、レビューの初動を早める構成にできた。

面接で話す補助資料は [docs/INTERVIEW_GUIDE.md](./docs/INTERVIEW_GUIDE.md) に整理しています。

## 設計思想

金額や明細は厳密な型で保持し、AIは説明補助に限定しました。ルールベースとAIの責務を分離すると、実務で説明責任を果たしやすくなります。

### なぜこの設計にしたのか

- ルーティング、ユースケース、永続化、AI呼び出しを分離して、責務を明確にするため。
- `mock` と `openai` を切り替えられるようにして、ローカル開発と本番連携を両立するため。
- 解析結果を元データと別テーブルで持ち、再生成と監査をしやすくするため。
- 認証、例外整形、入力制約を最初から入れ、実務に近い非機能要件まで示すため。

## 技術スタック

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- SQLite（`DATABASE_URL` を差し替えれば Postgres に移行可能）
- OpenAI互換API / mock provider
- Pytest / Ruff / Black / Mypy
- Docker / GitHub Actions

## ディレクトリ構成

```text
.
├── .env.example
├── .github/workflows/ci.yml
├── app
│   ├── api/routes.py
│   ├── core/config.py
│   ├── core/errors.py
│   ├── core/security.py
│   ├── db.py
│   ├── main.py
│   ├── models.py
│   ├── repositories.py
│   ├── schemas.py
│   └── services
│       ├── ai.py
│       └── domain.py
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── README.md
└── tests
    ├── conftest.py
    ├── test_health.py
    └── test_workflow.py
```

## API概要

- `POST /invoices`: 請求書を登録
- `GET /invoices/{id}`: 請求書を取得
- `POST /invoices/{id}/review`: AI解析を実行
- `GET /invoices/{id}/review`: 解析結果を取得

## 最小実装コード例

```python
@router.post(
    "/invoices/{record_id}/review",
    response_model=schemas.InvoiceReviewResponse,
    dependencies=[Depends(verify_internal_api_key)],
)
def analyze_record(
    record_id: str,
    service: InvoiceService = Depends(get_service),
) -> schemas.InvoiceReviewResponse:
    return service.review_invoice(record_id)
```

## ローカル起動

```bash
cp .env.example .env
make install
make run
```

Dockerでも起動できます。

```bash
cp .env.example .env
docker compose up --build
```

デフォルトでは `AI_PROVIDER=mock` のため、外部AIキーなしで動作確認できます。

## テスト

```bash
make test
make lint
make typecheck
```

## セキュリティ配慮

- 金額データは float と JSON 明細に分けて検証し、不正な構造を早期に弾く。
- AIは最終承認者ではなく補助判定として扱い、保存される出力はレビューコメントとフラグに限定する。
- 環境変数でAIプロバイダを切り替えでき、ローカルでは外部送信なしでデモ可能にする。

## エラーハンドリング設計

- 請求書が見つからない場合は 404、AI障害は 502 として責務を分ける。
- 永続化エラー時は即時ロールバックし、二重登録や中途半端な更新を避ける。

## CI

GitHub Actions で以下を実行します。

- `ruff check .`
- `black --check .`
- `mypy app tests`
- `pytest`

## サンプルリクエスト

```bash
curl -X POST http://localhost:8000/invoices \
  -H "Content-Type: application/json" \
  -H "X-Internal-API-Key: dev-internal-key" \
  -d '{
  "vendor_name": "ACME Hosting",
  "invoice_number": "INV-2026-001",
  "currency": "JPY",
  "total_amount": 128000.0,
  "line_items": [
    {
      "description": "Hosting fee",
      "amount": "100000"
    },
    {
      "description": "Support surcharge",
      "amount": "28000"
    }
  ]
}'
```

## READMEテンプレとして使う場合の章立て

- 背景 / 課題設定
- コンセプト
- 設計思想
- 技術スタック
- ディレクトリ構成
- ローカル起動手順
- API仕様
- テスト / CI
- セキュリティ
- 今後の拡張
