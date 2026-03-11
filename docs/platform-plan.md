# FinVest Platform - 智能金融投资平台建设方案

## 一、项目概述

FinVest 是一个 AI 驱动的智能金融投资平台，具备自动信息采集、走势预测、多市场交易执行和资产管理能力。平台借鉴 BettaFish、MiroFish、Microsoft Qlib、OpenBB、FinGPT、FinRL、FinRobot 等开源项目的架构思路，构建一体化的投资决策与执行系统。

## 二、支持市场

| 市场 | 说明 |
| --- | --- |
| A股（沪深） | 沪深两市主板、创业板、科创板 |
| 美股 | 纳斯达克、NYSE |
| H股（港股） | 港股通、港交所直连 |
| 基金 | 公募基金、ETF |
| 债券 | 国债、企业债、可转债 |

## 三、系统架构（六层设计）

```text
┌─────────────────────────────────────────────────────┐
│                   用户层 (Frontend)                    │
│         Web App (Vue 3) + Mobile App (React Native)   │
├─────────────────────────────────────────────────────┤
│                  应用服务层 (Application)               │
│   投资组合管理 │ 风险评估 │ 投研报告 │ 策略回测         │
├─────────────────────────────────────────────────────┤
│                AI 决策引擎层 (AI Core)                  │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐            │
│  │ 情报分析  │ │ 走势预测  │ │ 交易执行   │            │
│  │(BettaFish │ │(MiroFish │ │(FinRL +   │            │
│  │ 模式)     │ │+ Qlib)   │ │自研引擎)  │            │
│  └──────────┘ └──────────┘ └───────────┘            │
│  ┌──────────┐ ┌──────────────────────┐              │
│  │ 金融LLM  │ │ 投研报告Agent         │              │
│  │(FinGPT)  │ │(FinRobot模式)        │              │
│  └──────────┘ └──────────────────────┘              │
├─────────────────────────────────────────────────────┤
│              数据集成层 (Data Integration)              │
│   OpenBB统一数据接口 + 自建爬虫 + 券商/交易所API        │
├─────────────────────────────────────────────────────┤
│              券商/交易所对接层 (Broker Gateway)          │
│   A股(券商API) │ 美股(Alpaca/IB) │ H股(港股通/富途     │
│   OpenAPI/盈透) │ 基金(天天基金) │ 债券(券商固收/交易所) │
├─────────────────────────────────────────────────────┤
│              基础设施层 (Infrastructure)                │
│   PostgreSQL │ TimescaleDB │ Redis │ Kafka │ K8s     │
└─────────────────────────────────────────────────────┘
```

## 四、五大核心模块

### 4.1 信息自动采集模块

- **参考**: BettaFish 的 MindSpider 爬虫架构 + OpenBB 数据接口
- **数据源**:
  - 行情数据: AKShare、Tushare、Yahoo Finance、富途 OpenAPI、长桥 API
  - 财经新闻: 新浪财经、东方财富、Bloomberg、Reuters
  - 舆情数据: 微博、雪球、StockTwits、Reddit (r/wallstreetbets)
  - 公司公告: 巨潮资讯、SEC Edgar、港交所披露易
  - 宏观数据: 央行公告、统计局、美联储 FRED
  - 债券数据: 中国债券信息网、上清所、中证估值
- **输出**: 结构化事件流，实时推送至 Kafka

### 4.2 AI 预测引擎

- **短期走势**: Qlib 的 ML 模型（LSTM / Transformer / TCN），处理K线+技术指标
- **中长期趋势**: MiroFish 多Agent平行世界模拟，注入宏观变量预测走势
- **情绪因子**: FinGPT 微调的金融LLM 做新闻/舆情情感分析
- **强化学习**: FinRL 的 DRL 算法（PPO / SAC / DDPG）做动态仓位管理
- **债券模型**: 利率期限结构预测、信用利差模型、久期/凸性分析
- **港股因子**: AH股溢价因子、南向资金流、港币汇率因子

### 4.3 交易执行模块

- **A股通道**: 券商API（华泰 easytrader 等）
- **美股通道**: Alpaca API / Interactive Brokers TWS API
- **H股通道**: 港股通（额度管理）/ 富途 OpenD / 盈透 IB Gateway
- **基金通道**: 天天基金 / 蛋卷基金 API
- **债券通道**: 券商固收柜台 / 交易所债券撮合
- **功能**: 策略回测、模拟盘、实盘交易、止盈止损、可转债打新

### 4.4 账户与资产管理模块

- **多账户聚合**: 统一管理不同平台投资账户
- **资产看板**: 总资产、持仓分布、盈亏统计、风险敞口
- **分类视图**: 股票（A/美/H）、基金、债券独立看板
- **债券专属**: 到期收益率、持有期收益、票息日历
- **AH联动**: 同一公司A/H股价差监控
- **资金流水**: 充值/提现/调仓记录，税务报告生成

### 4.5 风控系统

- **通用风控**: 最大回撤限制、单日亏损上限、持仓集中度告警
- **债券风控**: 信用评级监控、久期匹配、利率敏感性预警
- **港股风控**: 汇率风险提示、港股通额度监控
- **合规检查**: 持仓比例、交易频率、关联交易检测

### 4.6 投研报告与智能助手

- **参考**: FinRobot 自动投研报告
- **功能**: 个股分析、行业对比、财务分析、债券评级报告
- **交互**: 金融LLM对话式投资助手，自然语言查询

## 五、技术栈

| 层级 | 技术选型 |
| --- | --- |
| 前端 | Vue 3 + TypeScript + TailwindCSS + ECharts |
| 移动端 | React Native |
| 后端 | Python (FastAPI) + Go (高并发交易网关) |
| AI框架 | PyTorch + HuggingFace + LangChain / AutoGen |
| 债券定价 | QuantLib |
| 数据接口 | OpenBB + AKShare + 富途 OpenAPI SDK + 长桥 SDK |
| 数据库 | PostgreSQL (业务) + TimescaleDB (时序) + Redis (缓存) |
| 消息队列 | Kafka (行情流) + RabbitMQ (任务调度) |
| 部署 | Docker + Kubernetes + Prometheus + Grafana |

## 六、风险提示

1. **合规风险**: 涉及代客理财需持有相关金融牌照（基金销售/投顾牌照）
2. **数据合规**: 爬虫采集需遵守各平台 ToS，券商API接入需正式合作协议
3. **AI预测局限**: 任何模型都无法保证盈利，需明确风险提示
4. **资金安全**: 采用用户自有账户+授权交易模式，平台不碰用户资金

## 七、参考项目

| 项目 | GitHub | Stars | 借鉴点 |
| --- | --- | --- | --- |
| OpenBB | github.com/OpenBB-finance/OpenBB | 62.7k | 数据集成层 |
| Microsoft Qlib | github.com/microsoft/qlib | 38.5k | ML预测引擎 |
| BettaFish | github.com/666ghj/BettaFish | 37k | 多Agent舆情采集 |
| FinGPT | github.com/AI4Finance-Foundation/FinGPT | 18.8k | 金融LLM |
| FinRL | github.com/AI4Finance-Foundation/FinRL | 14.1k | 强化学习交易 |
| MiroFish | github.com/666ghj/MiroFish | 8k | 平行世界预测 |
| FinRobot | github.com/AI4Finance-Foundation/FinRobot | 6.4k | 投研报告Agent |
