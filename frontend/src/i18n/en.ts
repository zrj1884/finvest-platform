export default {
  // Navigation
  nav: {
    dashboard: 'Dashboard',
    aShare: 'A-Share',
    usStock: 'US Stock',
    hkStock: 'HK Stock',
    fund: 'Fund',
    bond: 'Bond',
    news: 'News',
    aiReport: 'AI Report',
    sentiment: 'Sentiment',
    trading: 'Trading',
    portfolio: 'Portfolio',
    signIn: 'Sign In',
    logout: 'Logout',
  },

  // Common
  common: {
    loading: 'Loading...',
    symbol: 'Symbol',
    name: 'Name',
    market: 'Market',
    account: 'Account',
    quantity: 'Quantity',
    qty: 'Qty',
    price: 'Price',
    side: 'Side',
    buy: 'Buy',
    sell: 'Sell',
    status: 'Status',
    time: 'Time',
    cancel: 'Cancel',
    create: 'Create',
    reset: 'Reset',
    type: 'Type',
    amount: 'Amount',
    noData: 'No data',
  },

  // Markets
  market: {
    a_share: 'A-Share',
    us_stock: 'US Stock',
    hk_stock: 'HK Stock',
    fund: 'Fund',
    bond: 'Bond',
  },

  // Login
  login: {
    title: 'FinVest',
    signIn: 'Sign in to your account',
    createAccount: 'Create your account',
    email: 'Email',
    emailPlaceholder: 'you@example.com',
    password: 'Password',
    passwordPlaceholder: 'Min 6 characters',
    nickname: 'Nickname',
    nicknamePlaceholder: 'Optional',
    submit: 'Sign In',
    register: 'Register',
    waiting: 'Please wait...',
    switchToRegister: "Don't have an account? Register",
    switchToLogin: 'Already have an account? Sign in',
    requestFailed: 'Request failed',
    networkError: 'Network error',
  },

  // Trading
  trading: {
    title: 'Trading',
    manageAccounts: 'Manage Accounts',
    createAccount: 'Create Account',
    noAccounts: 'No trading accounts yet.',
    placeOrder: 'Place Order',
    symbolPlaceholder: 'e.g. 600519',
    marketOrder: 'Market',
    limitOrder: 'Limit',
    submitting: 'Submitting...',
    symbolRequired: 'Symbol is required',
    qtyRequired: 'Quantity must be greater than 0',
    lotSizeError: 'Buy quantity must be a multiple of {lot}',
    priceRequired: 'Price is required for limit orders',
    orderFailed: 'Failed to place order',
    cancelConfirm: 'Cancel this order?',
  },

  // Orders
  order: {
    title: 'Orders',
    noOrders: 'No orders',
    filled: 'Filled',
    filledPrice: 'Filled',
    type: 'Type',
    // Status
    pending: 'Pending',
    submitted: 'Submitted',
    partial_filled: 'Partial',
    cancelled: 'Cancelled',
    rejected: 'Rejected',
  },

  // Positions
  position: {
    title: 'Positions',
    noPositions: 'No positions',
    avgCost: 'Avg Cost',
    marketValue: 'Market Value',
    pnl: 'P&L',
    avail: 'Avail',
  },

  // Accounts
  accounts: {
    title: 'Accounts',
    newAccount: 'New Account',
    noAccounts: 'No accounts yet. Create one to start trading.',
    simulated: 'Simulated',
    created: 'Created',
    trade: 'Trade',
    resetConfirm: 'Reset this account? All positions and orders will be cleared.',
    creating: 'Creating...',
    marketOptions: {
      a_share: 'A-Share (沪深A股)',
      us_stock: 'US Stock (美股)',
      hk_stock: 'HK Stock (港股)',
      fund: 'Fund (基金)',
      bond: 'Bond (债券)',
    },
  },

  // Portfolio
  portfolio: {
    title: 'Portfolio',
    totalAssets: 'Total Assets',
    cashBalance: 'Cash Balance',
    marketValue: 'Market Value',
    totalPnl: 'Total P&L',
    unrealizedPnl: 'Unrealized P&L',
    realizedPnl: 'Realized P&L',
    accountCount: 'Accounts',
    performance: 'Portfolio Performance',
    allocation: 'Asset Allocation',
    holdings: 'Holdings',
    cashFlows: 'Recent Cash Flows',
    noTransactions: 'No transactions yet',
    noAccounts: 'No trading accounts yet.',
    createAccount: 'Create Account',
    pnlPct: 'P&L %',
  },

  // Home / Dashboard
  home: {
    title: 'Dashboard',
    aShare: { subtitle: 'A-Share Market', name: 'Shanghai / Shenzhen', desc: 'A stock daily data, realtime quotes' },
    usStock: { subtitle: 'US Stock Market', name: 'NYSE / NASDAQ', desc: 'US equity daily data via yfinance' },
    hkStock: { subtitle: 'HK Stock Market', name: 'HKEX', desc: 'Hong Kong stock daily data' },
    fund: { subtitle: 'Funds', name: 'Open-End Funds', desc: 'Fund NAV history and tracking' },
    bond: { subtitle: 'Bonds', name: 'Convertible Bonds', desc: 'Bond daily data and yields' },
    news: { subtitle: 'News', name: 'Financial News Feed', desc: 'Sina Finance, East Money, Xueqiu' },
  },

  // Table / Pagination
  table: {
    search: 'Search',
    searchPlaceholder: 'Symbol or name',
    pageSize: 'Per page',
    items: 'items',
    total: '{total} total',
    page: 'Page {page} / {pages}',
    prev: 'Prev',
    next: 'Next',
    noData: 'No data available. Data will appear after collection runs.',
    close: 'Close',
    changePct: 'Change %',
    volume: 'Volume',
    date: 'Date',
    nav: 'NAV',
    accNav: 'Acc. NAV',
    dailyReturn: 'Daily Return',
    bondType: 'Type',
    ytm: 'YTM',
  },

  // News
  news: {
    title: 'Financial News',
    relatedNews: 'Related News',
    noNews: 'No related news found',
    noArticles: 'No news available.',
    searchPlaceholder: 'Search news...',
    allSources: 'All Sources',
    sinaFinance: 'Sina Finance',
    eastMoney: 'East Money',
    xueqiu: 'Xueqiu',
    sentiment: 'Sentiment',
  },

  // AI Report
  report: {
    title: 'AI Research Reports',
    symbolPlaceholder: 'Enter stock symbol...',
    apiHint: 'Requires LLM API key (DeepSeek/Qwen/OpenAI) configured in backend .env',
    analyzingData: 'Analyzing data and generating report...',
    generateFailed: 'Failed to generate report. Check LLM API key configuration.',
    generatedAt: 'Generated at',
    emptyHint: 'Enter a stock symbol above to generate an AI research report.',
    tokens: 'tokens',
  },

  // Sentiment
  sentiment: {
    title: 'Market Sentiment',
    avgSentiment: 'Average Sentiment',
    bullishArticles: 'Bullish Articles',
    bearishArticles: 'Bearish Articles',
    neutralUnscored: 'Neutral / Unscored',
    distribution: 'Sentiment Distribution',
    veryBullish: 'Very Bullish',
    bullish: 'Bullish',
    neutral: 'Neutral',
    bearish: 'Bearish',
    veryBearish: 'Very Bearish',
    na: 'N/A',
    noArticles: 'No news articles available.',
  },

  // Detail pages
  detail: {
    open: 'Open',
    high: 'High',
    low: 'Low',
    daily: 'Daily',
    weekly: 'Weekly',
    monthly: 'Monthly',
    aiAnalysis: 'AI Analysis',
    generateReport: 'Generate Report',
    generating: 'Generating...',
    analyzingAI: 'Analyzing with AI...',
    clickGenerate: 'Click "Generate Report" to get AI-powered analysis',
  },

  // Charts
  chart: {
    total: 'Total',
    fullscreen: 'Fullscreen',
    exitFullscreen: 'Exit Fullscreen',
    noData: 'No chart data available',
    loading: 'Loading chart...',
  },
}
