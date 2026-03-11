# FinVest Platform

AI 驱动的智能金融投资平台，具备自动信息采集、走势预测、多市场交易执行和资产管理能力。

## 支持市场

| 市场 | 说明 |
| --- | --- |
| A股 | 沪深主板、创业板、科创板 |
| 美股 | 纳斯达克、NYSE |
| H股 | 港股通、港交所 |
| 基金 | 公募基金、ETF |
| 债券 | 国债、企业债、可转债 |

## 技术栈

- **后端**: Python 3.11 + FastAPI + SQLAlchemy + Alembic
- **前端**: Vue 3 + TypeScript + Vite + TailwindCSS
- **AI**: PyTorch + HuggingFace + LangChain
- **数据库**: PostgreSQL + TimescaleDB + Redis
- **消息队列**: Kafka + RabbitMQ
- **部署**: Docker + Kubernetes

## 项目结构

```
finvest-platform/
├── backend/          # FastAPI 后端服务
├── frontend/         # Vue 3 前端应用
├── infra/            # 基础设施配置（K8s, Terraform 等）
├── scripts/          # 运维与工具脚本
├── docs/             # 项目文档
├── docker-compose.yml
└── .github/workflows/  # CI/CD
```

## 快速开始

### 环境要求

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- Poetry

### 本地开发

1. 克隆仓库

```bash
git clone https://github.com/zrj1884/finvest-platform.git
cd finvest-platform
```

2. 启动基础设施（数据库、缓存）

```bash
docker compose up -d postgres redis
```

3. 启动后端

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

5. 一键启动所有服务（Docker）

```bash
docker compose up -d
```

- 后端 API: http://localhost:8000
- 前端应用: http://localhost:3000
- API 文档: http://localhost:8000/docs

## 开发规范

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT
