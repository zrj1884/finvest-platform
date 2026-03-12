# 交易系统开发任务清单

## 一、用户反馈的问题修复

### T1. 记忆最后选择的资金账户 [P1]
- TradingView.vue: `selectedAccountId` 在页面刷新后丢失
- 方案: localStorage 保存选中的 accountId，加载时恢复；AccountsView "交易" 按钮传 `?account=ID`，TradingView 读取 query param
- 涉及文件: `TradingView.vue`, `AccountsView.vue`

### T2. A股代码候选列表（自动补全）[P1]
- 当前 OrderPanel 只有普通文本框，无补全
- 方案: 新建 `SymbolAutocomplete.vue`，根据账户市场类型调用后端搜索接口返回 `[{symbol, name}]` 候选列表
- 后端: 新增 `GET /v1/market/search?market=a_share&q=600`，查 stock_daily 去重返回 symbol+name
- 涉及文件: 新建 `SymbolAutocomplete.vue`，修改 `OrderPanel.vue`，新增后端接口

### T3. 买入后持仓列表未刷新 [P0]
- `onOrderPlaced` 中 refresh() 与 loadAccounts() 无 await，存在竞态
- 方案: await 所有刷新操作，确保顺序执行

### T4. 卖出后委托列表未刷新 [P0]
- 同 T3，统一修复 onOrderPlaced 的刷新逻辑

## 二、交易核心功能补全

### T5. 下单表单验证增强 [P1]
- 数量不能为 0 或负数
- A股买入数量必须是 100 的整数倍
- 可转债买入数量必须是 10 的整数倍
- 卖出数量不能超过可用数量（前端预校验）

### T6. 下单成功后清空表单 [P1]
- OrderPanel.vue: 成功后 symbol/quantity/price 未重置

### T7. 撤单操作增加确认弹窗 [P2]
- OrderList.vue: 撤单按钮直接调 API，无确认

### T8. 委托列表分页 [P2]
- 当前硬编码 limit=50，无分页 UI
- 后端需增加 offset 参数（T13）

### T9. 持仓表增加排序功能 [P3]

## 三、业务逻辑完善（后端）

### T10. 风控检查强制执行 [P0]
- trading.py: pre_trade_check() 返回错误列表但未阻断下单
- 方案: 风控不通过时返回 400 错误

### T11. T+1 交割限制 [P2]
- A股买入当天 available_quantity=0，需每日定时任务释放

### T12. 组合快照定时任务 [P2]
- snapshot.py 的 record_snapshot() 已实现但未注册到调度器

### T13. 后端委托列表增加 offset 参数 [P2]
- 当前 list_by_account 只有 limit，无 offset

## 四、用户体验优化

### T14. 盈亏颜色规范统一 [P3]
### T15. 日期格式国际化 [P2]
### T16. 交易页面 i18n 补全 [P2]
### T17. 下单错误信息展示优化 [P3]
### T18. 账户管理页面优化 [P3]

## 优先级排序

| 优先级 | 任务 | 复杂度 |
|--------|------|--------|
| P0 紧急 | T3+T4 数据刷新修复 | 低 |
| P0 紧急 | T10 风控强制执行 | 低 |
| P1 重要 | T1 记忆选中账户 | 低 |
| P1 重要 | T2 A股代码自动补全 | 中 |
| P1 重要 | T5 表单验证增强 | 低 |
| P1 重要 | T6 成功后清空表单 | 低 |
| P2 改进 | T7 撤单确认弹窗 | 低 |
| P2 改进 | T8+T13 委托分页 | 中 |
| P2 改进 | T11 T+1 交割释放 | 中 |
| P2 改进 | T12 组合快照任务 | 低 |
| P2 改进 | T15+T16 i18n补全 | 低 |
| P3 优化 | T9 持仓排序 | 低 |
| P3 优化 | T14 颜色统一检查 | 低 |
| P3 优化 | T17+T18 UX优化 | 低 |
