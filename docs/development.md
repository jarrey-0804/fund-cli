# 开发指南

## 环境搭建

```bash
# 克隆项目
git clone https://github.com/your-org/fund-cli.git
cd fund-cli

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装开发依赖
pip install -e ".[dev]"

# 安装 pre-commit 钩子
pre-commit install
```

## 项目结构

```
src/fund_cli/
├── cli.py          # CLI入口
├── config.py       # 配置管理
├── core/           # 核心模块
├── data/           # 数据层
├── analysis/       # 分析模块
├── commands/       # CLI命令
├── views/          # 视图层
├── ai/             # AI模块 (V2.0)
└── utils/          # 工具模块
```

## 代码规范

- 格式化: `black src tests --target-version py310`
- Lint: `ruff check src tests`
- 类型检查: `mypy src`
- 测试: `pytest tests/ -v`

## 添加新命令

1. 在 `src/fund_cli/commands/` 下创建 `xxx_cmd.py`
2. 使用 `typer.Typer()` 创建子应用
3. 在 `cli.py` 中注册子命令
4. 在 `tests/unit/test_commands/` 下添加测试

## 添加新数据源

1. 继承 `DataSourceAdapter` 基类
2. 实现所有抽象方法
3. 在 `data_manager.py` 中注册
