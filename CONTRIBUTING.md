# 贡献指南

感谢您对Fund CLI项目的关注！

## 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/your-org/fund-cli.git
cd fund-cli

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 安装pre-commit钩子
pre-commit install
```

## 代码提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型说明

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例

```
feat(ai): add Qwen provider support

Add Alibaba Cloud Qwen LLM provider for AI analysis.
Supports qwen-max, qwen-plus, and qwen-turbo models.

Closes #123
```

## 代码审查流程

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交变更 (`git commit -m 'feat: add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 测试要求

- 新功能必须包含单元测试
- 测试覆盖率不得低于80%
- 所有测试必须通过

```bash
# 运行测试
pytest tests/ -v

# 运行测试并检查覆盖率
pytest tests/ --cov=src/fund_cli --cov-report=html

# 代码格式化
black src tests --line-length=100

# 代码检查
ruff check src tests
```

## 问题反馈

如果您发现了bug或有功能建议，请通过以下方式反馈：

1. 查看现有Issue，避免重复提交
2. 创建新Issue，详细描述问题
3. 对于bug，请提供复现步骤和环境信息

## 许可证

通过贡献代码，您同意您的贡献将在MIT许可证下发布。
