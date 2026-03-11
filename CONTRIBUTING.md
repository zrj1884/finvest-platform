# 贡献指南

## 分支策略

- `main` - 生产分支，保持稳定
- `develop` - 开发主分支
- `feature/*` - 功能分支，从 develop 拉出
- `fix/*` - 修复分支
- `release/*` - 发布分支

## 开发流程

1. 从 `develop` 创建功能分支：`feature/xxx`
2. 开发完成后提交 PR 到 `develop`
3. 通过 CI 检查和 Code Review 后合并
4. 定期从 `develop` 合并到 `main` 发布

## 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <description>

[optional body]
```

类型：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档变更
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具变更

示例：
```
feat(backend): add user authentication API
fix(frontend): resolve chart rendering issue on mobile
docs: update API documentation
```

## 代码规范

### 后端 (Python)

- 使用 `ruff` 进行代码检查和格式化
- 使用 `mypy` 进行类型检查
- 遵循 PEP 8 规范
- 所有 API 接口编写测试

```bash
cd backend
poetry run ruff check app/
poetry run ruff format app/
poetry run mypy app/ --ignore-missing-imports
poetry run pytest tests/ -v
```

### 前端 (TypeScript)

- 使用 ESLint + Prettier
- 组件使用 `<script setup>` 语法
- 使用 Composition API

```bash
cd frontend
npm run lint
npm run build
```

## PR 要求

- 描述清楚改动内容和原因
- CI 检查全部通过
- 至少 1 人 Code Review
- 新功能需要包含测试
