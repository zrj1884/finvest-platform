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
    priceRequired: '限价单需填写价格',
    orderFailed: '下单失败',
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

  // Charts
  chart: {
    total: '总计',
  },
}
