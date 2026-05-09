# 贡献指南

感谢您对 Fund CLI 项目的关注！本文档将帮助您快速参与项目开发。

## 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/jarrey-0804/fund-cli.git
cd fund-cli

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 安装 pre-commit 钩子
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

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 Bug |
| `docs` | 文档更新 |
| `style` | 代码格式调整（不影响功能） |
| `refactor` | 代码重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具相关 |

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
- 核心模块测试覆盖率不低于 90%
- 整体测试覆盖率不低于 75%
- 所有测试必须通过

```bash
# 运行全部测试
pytest tests/ -v

# 运行测试并检查覆盖率
pytest tests/ --cov=src/fund_cli --cov-report=html

# 代码格式化
ruff format src tests

# 代码检查
ruff check src tests
```

## 文档贡献

我们欢迎文档改进！文档使用 MkDocs + Material for MkDocs 构建：

```bash
# 安装文档依赖
pip install -e ".[docs]"

# 本地预览（支持热重载）
mkdocs serve

# 构建
mkdocs build --strict
```

文档文件位于 `docs/` 目录，遵循以下规范：

- 使用中文撰写
- 使用标准 Markdown 语法（支持 MkDocs 扩展）
- 命令示例包含预期输出
- API 文档使用 `mkdocstrings` 自动生成

## PR 提交前检查清单

- [ ] 所有测试通过 (`pytest tests/ -v`)
- [ ] 代码检查通过 (`ruff check src/`)
- [ ] 类型检查通过 (`mypy src/fund_cli/core/ src/fund_cli/data/`)
- [ ] 新增功能有对应测试
- [ ] 文档已同步更新
- [ ] 遵循 Conventional Commits 提交规范

## 问题反馈

如果您发现了 Bug 或有功能建议，请通过以下方式反馈：

1. 查看现有 Issue，避免重复提交
2. 创建新 Issue，详细描述问题
3. 对于 Bug，请提供复现步骤和环境信息

## 许可证

通过贡献代码，您同意您的贡献将在 MIT 许可证下发布。

## 行为准则

本项目遵循 [贡献者公约](https://github.com/jarrey-0804/fund-cli/blob/main/CODE_OF_CONDUCT.md)，参与项目即表示同意遵守该准则。
