# FinVest Platform - 开发环境记录

本文档记录开发环境的状态变化，便于环境复现和问题排查。

---

## 开发机器

| 项目 | 值 |
|------|-----|
| 操作系统 | macOS 26.3.1 (Darwin) |
| 架构 | Apple Silicon (arm64) |
| Shell | zsh |

---

## 工具链版本

| 工具 | 版本 | 安装方式 | 说明 |
|------|------|---------|------|
| Git | 2.50.1 | Apple Git | 系统自带 |
| Python | 3.13.3 | Homebrew | pyproject.toml 要求 ^3.11 |
| Node.js | 23.11.0 | Homebrew | 前端构建 |
| npm | 10.9.2 | 随 Node.js | |
| Poetry | 2.1.3 | Homebrew | Python 依赖管理 |
| Docker CLI | 28.1.1 | Homebrew (`brew install --formula docker`) | 注意：`brew install --cask docker` 有 conflicts_with bug |
| Docker Compose | 2.36.1 | Homebrew (`brew install docker-compose`) | 需配置 `~/.docker/config.json` 的 `cliPluginsExtraDirs` |
| Colima | 0.8.1 | Homebrew | 轻量 Docker 运行时，替代 Docker Desktop |
| GitHub CLI | 2.73.0 | Homebrew | |

### Docker 安装注意事项

macOS 上 `brew install --cask docker`（Docker Desktop）有 `conflicts_with` 报错，改用 Colima 方案：

```bash
brew install --formula docker
brew install colima docker-compose

# 配置 docker-compose 插件路径
cat > ~/.docker/config.json << 'EOF'
{
  "cliPluginsExtraDirs": [
    "/opt/homebrew/lib/docker/cli-plugins"
  ]
}
EOF

# 启动 Colima（4核 8G 内存 60G 磁盘）
colima start --cpu 4 --memory 8 --disk 60
```

---

## 容器服务

| 服务 | 镜像 | 端口 | 容器名 |
|------|------|------|--------|
| PostgreSQL + TimescaleDB | `timescale/timescaledb:latest-pg16` | 5432 | finvest-postgres |
| Redis | `redis:7-alpine` | 6379 | finvest-redis |
| Prometheus | `prom/prometheus:latest` | 9090 | finvest-prometheus |
| Grafana | `grafana/grafana:latest` | 3001 | finvest-grafana |

### 数据库版本

| 组件 | 版本 |
|------|------|
| PostgreSQL | 16.11 |
| TimescaleDB | 2.25.2 |
| Redis | 7.4.8 |

### 本地访问地址与账户

| 服务 | 地址 | 用户名 | 密码 | 说明 |
|------|------|--------|------|------|
| PostgreSQL | `localhost:5432` | `finvest` | `finvest` | 数据库名: `finvest` |
| Redis | `localhost:6379` | - | 无密码 | DB 0 |
| 后端 API | `http://localhost:8000` | - | - | FastAPI，`--reload` 模式 |
| API 文档 (Swagger) | `http://localhost:8000/docs` | - | - | 自动生成 |
| API 文档 (ReDoc) | `http://localhost:8000/redoc` | - | - | 自动生成 |
| Health Check | `http://localhost:8000/health` | - | - | 返回 `{"status": "ok"}` |
| Prometheus Metrics | `http://localhost:8000/metrics` | - | - | FastAPI 自动暴露 |
| Prometheus UI | `http://localhost:9090` | - | - | 指标查询与图表 |
| Grafana | `http://localhost:3001` | `admin` | `finvest` | 监控仪表盘 |
| 前端 (Vite dev) | `http://localhost:5173` | - | - | `npm run dev` |
| 前端 (Docker) | `http://localhost:3000` | - | - | Nginx 容器 |
| GitHub 仓库 | `https://github.com/zrj1884/finvest-platform` | `zrj1884` | PAT token | `gh auth login --with-token` |

#### 连接字符串

```bash
# 后端应用连接
DATABASE_URL=postgresql+asyncpg://finvest:finvest@localhost:5432/finvest
REDIS_URL=redis://localhost:6379/0

# Docker 容器间连接（docker-compose 内部）
DATABASE_URL=postgresql+asyncpg://finvest:finvest@postgres:5432/finvest
REDIS_URL=redis://redis:6379/0

# psql 命令行连接
docker compose exec postgres psql -U finvest
```

---

## Python 虚拟环境

| 项目 | 值 |
|------|-----|
| 路径 | `~/Library/Caches/pypoetry/virtualenvs/finvest-backend-CN_pLAyi-py3.13` |
| Python | 3.13.3 |
| 管理工具 | Poetry |

关键依赖：
- FastAPI 0.115+
- SQLAlchemy 2.0+（需要 `greenlet` 用于 async + Alembic）
- asyncpg 0.30+
- Alembic 1.14+
- python-jose[cryptography] 3.3+（JWT）
- bcrypt 5.0+（密码哈希）
- slowapi 0.1+（API 限流）
- httpx 0.28+（OAuth HTTP 客户端）
- akshare 1.18+（A股/港股/基金/债券数据）
- yfinance 1.2+（美股数据）
- pandas 3.0+（数据处理）
- apscheduler 3.11+（定时任务调度）

---

## 数据库 Schema 状态

**Alembic 迁移版本**: `002` (Add user OAuth fields)

### 业务表

| 表名 | 说明 | 主键 |
|------|------|------|
| users | 用户（支持邮箱注册 + OAuth） | UUID |
| accounts | 交易账户（关联用户，支持 5 市场） | UUID |
| positions | 持仓 | UUID |
| orders | 订单（完整状态机） | UUID |

### 时序表（TimescaleDB Hypertable）

| 表名 | 说明 | 分区策略 |
|------|------|---------|
| stock_daily | 股票日线（A股/美股/港股） | 按月分区 |
| fund_nav | 基金净值 | 按月分区 |
| bond_daily | 债券日线 | 按月分区 |
| news_articles | 财经新闻 | 按周分区，保留 1 年 |

### 连续聚合视图

| 视图 | 源表 | 聚合粒度 | 自动刷新 |
|------|------|---------|---------|
| stock_weekly | stock_daily | 周 | 每天，回溯 1 月 |
| stock_monthly | stock_daily | 月 | 每天，回溯 3 月 |

---

## 环境变更日志

| 日期 | 变更内容 | 涉及组件 |
|------|---------|---------|
| 2026-03-11 | 初始化项目，安装全部工具链 | Git, Poetry, Node.js, gh |
| 2026-03-11 | 安装 Docker 环境（Colima + Docker CLI + Compose） | Docker, Colima |
| 2026-03-11 | 启动 PostgreSQL + TimescaleDB + Redis 容器 | postgres, redis |
| 2026-03-11 | 运行 Alembic 迁移 001，创建全部表和 hypertable | 数据库 |
| 2026-03-11 | 添加 greenlet 依赖，修复 Alembic async 迁移 | Python 依赖 |
| 2026-03-11 | S1.3: Redis Stream 消息总线、Prometheus + Grafana 监控、Sentry 集成 | Redis, Prometheus, Grafana, Sentry |
| 2026-03-11 | S1.4: 用户系统 — JWT 鉴权、邮箱注册/登录、OAuth(GitHub/Google)、API 限流 | 后端, 数据库 |
| 2026-03-11 | Alembic 迁移 002: users 表新增 oauth_provider/oauth_id 字段 | 数据库 |
| 2026-03-12 | S1.5: 行情数据采集服务 — A股/美股/港股/基金/债券数据采集、标准化、TimescaleDB 写入 | 后端 |
| 2026-03-12 | S1.6: 资讯与舆情采集 — 新浪财经/东方财富/雪球爬虫、宏观数据、APScheduler 定时调度 | 后端 |

---

## 常用命令

```bash
# 启动/停止容器
docker compose up -d postgres redis prometheus grafana
docker compose down

# 启动/停止 Colima
colima start --cpu 4 --memory 8 --disk 60
colima stop

# 运行数据库迁移
cd backend && poetry run alembic upgrade head

# 启动后端开发服务器
cd backend && poetry run uvicorn app.main:app --reload

# 启动前端开发服务器
cd frontend && npm run dev

# 一键初始化数据库
./scripts/init_db.sh
```
