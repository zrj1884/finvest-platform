export default {
  // Navigation
  nav: {
    dashboard: '首页',
    aShare: 'A股',
    usStock: '美股',
    hkStock: '港股',
    fund: '基金',
    bond: '债券',
    news: '资讯',
    aiReport: 'AI研报',
    sentiment: '舆情分析',
    trading: '交易',
    portfolio: '资产',
    signIn: '登录',
    logout: '退出',
  },

  // Common
  common: {
    loading: '加载中...',
    symbol: '代码',
    name: '名称',
    market: '市场',
    account: '账户',
    quantity: '数量',
    qty: '数量',
    price: '价格',
    side: '方向',
    buy: '买入',
    sell: '卖出',
    status: '状态',
    time: '时间',
    cancel: '取消',
    create: '创建',
    reset: '重置',
    type: '类型',
    amount: '金额',
    noData: '暂无数据',
  },

  // Markets
  market: {
    a_share: 'A股',
    us_stock: '美股',
    hk_stock: '港股',
    fund: '基金',
    bond: '债券',
  },

  // Login
  login: {
    title: 'FinVest',
    signIn: '登录账户',
    createAccount: '注册账户',
    email: '邮箱',
    emailPlaceholder: 'you@example.com',
    password: '密码',
    passwordPlaceholder: '至少6个字符',
    nickname: '昵称',
    nicknamePlaceholder: '可选',
    submit: '登录',
    register: '注册',
    waiting: '请稍候...',
    switchToRegister: '没有账户？立即注册',
    switchToLogin: '已有账户？立即登录',
    requestFailed: '请求失败',
    networkError: '网络错误',
  },

  // Trading
  trading: {
    title: '交易',
    manageAccounts: '管理账户',
    createAccount: '创建账户',
    noAccounts: '暂无交易账户',
    placeOrder: '下单',
    symbolPlaceholder: '如 600519',
    marketOrder: '市价',
    limitOrder: '限价',
    submitting: '提交中...',
    symbolRequired: '请输入代码',
    qtyRequired: '数量必须大于0',
    lotSizeError: '买入数量必须是 {lot} 的整数倍',
    priceRequired: '限价单需填写价格',
    orderFailed: '下单失败',
    cancelConfirm: '确认撤销此委托？',
  },

  // Orders
  order: {
    title: '委托',
    noOrders: '暂无委托',
    filled: '已成',
    filledPrice: '成交价',
    type: '类型',
    // Status
    pending: '待提交',
    submitted: '已提交',
    partial_filled: '部分成交',
    cancelled: '已撤销',
    rejected: '已拒绝',
  },

  // Positions
  position: {
    title: '持仓',
    noPositions: '暂无持仓',
    avgCost: '成本价',
    marketValue: '市值',
    pnl: '盈亏',
    avail: '可用',
  },

  // Accounts
  accounts: {
    title: '账户管理',
    newAccount: '新建账户',
    noAccounts: '暂无账户，请创建账户开始交易。',
    simulated: '模拟',
    created: '创建于',
    trade: '交易',
    resetConfirm: '确认重置账户？所有持仓和委托将被清除。',
    creating: '创建中...',
    marketOptions: {
      a_share: 'A股（沪深）',
      us_stock: '美股（NYSE/NASDAQ）',
      hk_stock: '港股（HKEX）',
      fund: '基金（开放式）',
      bond: '债券（可转债）',
    },
  },

  // Portfolio
  portfolio: {
    title: '资产概览',
    totalAssets: '总资产',
    cashBalance: '可用资金',
    marketValue: '持仓市值',
    totalPnl: '总盈亏',
    unrealizedPnl: '浮动盈亏',
    realizedPnl: '已实现盈亏',
    accountCount: '账户数',
    performance: '资产走势',
    allocation: '资产配置',
    holdings: '持仓明细',
    cashFlows: '资金流水',
    noTransactions: '暂无交易记录',
    noAccounts: '暂无交易账户',
    createAccount: '创建账户',
    pnlPct: '盈亏比例',
  },

  // Home / Dashboard
  home: {
    title: '首页看板',
    aShare: { subtitle: 'A股市场', name: '沪深A股', desc: 'A股日线数据、实时行情' },
    usStock: { subtitle: '美股市场', name: 'NYSE / NASDAQ', desc: '美股日线数据（yfinance）' },
    hkStock: { subtitle: '港股市场', name: 'HKEX', desc: '港股日线数据' },
    fund: { subtitle: '基金', name: '开放式基金', desc: '基金净值走势与追踪' },
    bond: { subtitle: '债券', name: '可转债', desc: '债券日线数据与收益率' },
    news: { subtitle: '资讯', name: '财经新闻', desc: '新浪财经、东方财富、雪球' },
  },

  // Table / Pagination
  table: {
    search: '搜索',
    searchPlaceholder: '代码或名称',
    pageSize: '每页',
    items: '条',
    total: '共 {total} 条',
    page: '第 {page} / {pages} 页',
    prev: '上一页',
    next: '下一页',
    noData: '暂无数据，数据将在采集后显示。',
    close: '收盘价',
    changePct: '涨跌幅',
    volume: '成交量',
    date: '日期',
    nav: '净值',
    accNav: '累计净值',
    dailyReturn: '日收益率',
    bondType: '类型',
    ytm: '到期收益率',
  },

  // News
  news: {
    title: '财经资讯',
    relatedNews: '相关资讯',
    noNews: '暂无相关资讯',
    noArticles: '暂无资讯',
    searchPlaceholder: '搜索资讯...',
    allSources: '全部来源',
    sinaFinance: '新浪财经',
    eastMoney: '东方财富',
    xueqiu: '雪球',
    sentiment: '情绪',
  },

  // AI Report
  report: {
    title: 'AI 研究报告',
    symbolPlaceholder: '输入股票代码...',
    apiHint: '需要在后端 .env 中配置 LLM API 密钥（DeepSeek/Qwen/OpenAI）',
    analyzingData: '正在分析数据并生成报告...',
    generateFailed: '生成报告失败，请检查 LLM API 密钥配置',
    generatedAt: '生成时间',
    emptyHint: '在上方输入股票代码，生成 AI 研究报告',
    tokens: 'tokens',
  },

  // Sentiment
  sentiment: {
    title: '市场舆情分析',
    avgSentiment: '平均情绪',
    bullishArticles: '看多文章',
    bearishArticles: '看空文章',
    neutralUnscored: '中性 / 未评分',
    distribution: '情绪分布',
    veryBullish: '强烈看多',
    bullish: '看多',
    neutral: '中性',
    bearish: '看空',
    veryBearish: '强烈看空',
    na: '未评分',
    noArticles: '暂无资讯文章',
  },

  // Detail pages
  detail: {
    open: '开盘价',
    high: '最高价',
    low: '最低价',
    daily: '日线',
    weekly: '周线',
    monthly: '月线',
    aiAnalysis: 'AI 分析',
    generateReport: '生成研报',
    generating: '生成中...',
    analyzingAI: 'AI 分析中...',
    clickGenerate: '点击「生成研报」获取 AI 智能分析',
  },

  // Charts
  chart: {
    total: '总计',
    fullscreen: '全屏',
    exitFullscreen: '退出全屏',
    noData: '暂无图表数据',
    loading: '加载图表中...',
  },
}
