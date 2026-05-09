# 开发指南

## 环境搭建

```bash
# 克隆项目
git clone https://github.com/jarrey-0804/fund-cli.git
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

详细指南请参见下方 [添加新数据源适配器](#添加新数据源适配器) 章节。

---

## 架构设计

### 多数据源架构

Fund CLI 采用适配器模式实现多数据源统一访问，核心设计如下：

```
                    ┌──────────────┐
                    │  DataManager  │  统一入口
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │ DataSource   │  网关层（路由、缓存、降级）
                    │ Gateway      │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────┴──┐  ┌─────┴────┐  ┌───┴──────┐
     │ AKShare   │  │ Tushare  │  │  Wind    │
     │ Adapter   │  │ Adapter  │  │  Adapter │
     └───────────┘  └──────────┘  └──────────┘
```

- **DataSourceAdapter** (`fund_cli.data.base`): 抽象基类，定义统一的数据获取接口
- **DataSourceGateway** (`fund_cli.core.data_gateway`): 网关层，负责数据源路由、结果缓存和故障降级
- **DataNormalizer** (`fund_cli.data.normalizer`): 数据标准化，将不同数据源的原始数据统一为内部格式
- **DataManager** (`fund_cli.core.data_manager`): 面向用户的高级 API，屏蔽底层实现细节

### 报告引擎

报告生成采用模板引擎 + 多格式输出的分层架构：

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Analysis   │────▶│ TemplateEngine   │────▶│    Reporter     │
│  Result     │     │ (Jinja2 渲染)     │     │  (格式化输出)    │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                      │
                              ┌───────────┬───────────┼───────────┐
                              │           │           │           │
                         ┌────┴───┐ ┌────┴───┐ ┌────┴──┐ ┌────┴───┐
                         │  HTML  │ │  PDF   │ │ DOCX  │ │  PPTX  │
                         └────────┘ └────────┘ └───────┘ └────────┘
```

- **TemplateEngine**: 使用 Jinja2 模板引擎，将分析结果渲染为 HTML
- **Reporter** (基类): 定义报告生成的统一接口
- **各格式 Reporter**: 继承基类，实现 HTML、PDF、Word、PPT 等格式输出
- 模板文件位于 `src/fund_cli/templates/` 目录

### AI Agent

AI 模块基于 LangGraph 构建智能分析 Agent：

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  用户查询    │────▶│  FundAgent   │────▶│  分析结果/报告   │
└─────────────┘     │ (LangGraph)  │     └─────────────────┘
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │   LLMProvider│  多模型支持
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────┴───┐  ┌────┴───┐  ┌────┴──────┐
         │ OpenAI │  │  Qwen  │  │  LiteLLM  │
         └────────┘  └────────┘  └───────────┘
```

- **FundAgent**: 基于 LangGraph 的状态机，编排分析流程
- **LLMProvider**: 抽象基类，支持 OpenAI、通义千问、LiteLLM 等多种后端
- **Tools**: Agent 可调用的工具集（数据查询、分析计算、报告生成等）

---

## 添加新数据源适配器 {#添加新数据源适配器}

以下步骤演示如何添加一个新的数据源适配器（以示例 "CustomSource" 为例）：

### 1. 创建适配器类

在 `src/fund_cli/data/adapters/` 下创建 `custom_adapter.py`：

```python
from fund_cli.data.base import DataSourceAdapter
from fund_cli.data.models import FundInfo, NavData
from typing import Optional


class CustomSourceAdapter(DataSourceAdapter):
    """CustomSource 数据源适配器。"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(name="custom_source")
        self._api_key = api_key

    async def get_fund_info(self, fund_code: str) -> FundInfo:
        """获取基金基本信息。"""
        # 实现数据获取逻辑
        ...

    async def get_fund_nav(self, fund_code: str, start_date: str, end_date: str) -> list[NavData]:
        """获取基金净值数据。"""
        # 实现数据获取逻辑
        ...
```

### 2. 实现必要方法

适配器必须实现 `DataSourceAdapter` 基类的所有抽象方法：

- `get_fund_info(fund_code)` - 基金信息查询
- `get_fund_nav(fund_code, start_date, end_date)` - 净值数据查询
- `search_funds(keyword)` - 基金搜索
- 其他业务所需的数据获取方法

### 3. 注册适配器

在 `src/fund_cli/core/data_manager.py` 中注册新适配器：

```python
from fund_cli.data.adapters.custom_adapter import CustomSourceAdapter

# 在 DataManager.__init__ 中注册
self._gateways["custom_source"] = CustomSourceAdapter(api_key=config.get("custom_api_key"))
```

### 4. 添加配置项

在配置文件中添加新数据源所需的配置项（API Key、超时时间等）。

### 5. 编写测试

在 `tests/unit/test_data/` 下创建 `test_custom_adapter.py`，覆盖所有公开方法。

---

## 添加新报告格式

以下步骤演示如何添加新的报告输出格式（以示例 "ExcelReporter" 为例）：

### 1. 创建 Reporter 类

在 `src/fund_cli/core/reporters/` 下创建 `excel_reporter.py`：

```python
from fund_cli.core.reporter import Reporter
from fund_cli.core.ai_analyzer import AnalysisResult


class ExcelReporter(Reporter):
    """Excel 格式报告生成器。"""

    def generate(self, result: AnalysisResult, output_path: str) -> str:
        """生成 Excel 报告。"""
        # 实现 Excel 生成逻辑
        ...

    @property
    def format_name(self) -> str:
        return "excel"

    @property
    def file_extension(self) -> str:
        return ".xlsx"
```

### 2. 注册 Reporter

在 `src/fund_cli/core/reporters/__init__.py` 中导出新类，并在 `Reporter` 工厂中注册。

### 3. 添加 CLI 支持

在 `src/fund_cli/commands/report_cmd.py` 中添加新的格式选项。

### 4. 编写测试

在 `tests/unit/test_core/` 下添加对应测试文件。

---

## 文档构建

项目使用 [MkDocs](https://www.mkdocs.org/) + [mkdocstrings](https://mkdocstrings.github.io/) 构建文档。

### 本地预览

```bash
# 启动开发服务器（支持热重载）
mkdocs serve

# 指定端口
mkdocs serve -a 127.0.0.1:8080
```

### 构建生产版本

```bash
# 构建静态站点到 site/ 目录
mkdocs build

# 构建时严格检查链接
mkdocs build --strict
```

### 文档结构

```
docs/
├── index.md              # 首页
├── installation.md       # 安装指南
├── development.md        # 开发指南（本文件）
├── usage/
│   └── tutorial.md       # 使用教程
└── api/
    ├── reference.md      # API 索引
    ├── core.md           # 核心模块
    ├── analysis.md       # 分析模块
    ├── ai.md             # AI 模块
    ├── data.md           # 数据层
    ├── optimizers.md     # 优化器
    └── reporters.md      # 报告生成器
```

### API 文档自动生成

API 文档使用 mkdocstrings 的 `:::` 语法从源码 docstring 自动生成。编写代码时请遵循以下规范：

- 所有公开类和函数必须包含 Google 风格的 docstring
- 使用类型注解标注参数和返回值类型
- 复杂逻辑应在 docstring 中提供使用示例

---

## Makefile 命令参考

| 命令 | 说明 |
|------|------|
| `make help` | 显示所有可用命令 |
| `make install` | 安装开发依赖（`pip install -e ".[dev]"`） |
| `make test` | 运行测试（`pytest tests/ -v --tb=short`） |
| `make test-cov` | 运行测试并生成覆盖率报告 |
| `make lint` | 代码检查（ruff + mypy） |
| `make format` | 格式化代码（black + ruff --fix） |
| `make build` | 构建 Python 包（`python -m build`） |
| `make docker` | 构建 Docker 镜像 |
| `make clean` | 清理构建产物和缓存 |

---

## CI/CD 流程说明

### 持续集成（CI）

CI 流水线在以下事件触发：

- **Push** 到 `main` 或 `develop` 分支
- **Pull Request** 目标为 `main` 分支

CI 流水线包含以下阶段：

1. **测试** (矩阵策略): 在 Python 3.10、3.11、3.12 三个版本上并行运行
   - 安装依赖
   - Ruff 代码检查
   - Mypy 类型检查
   - Pytest 测试 + 覆盖率生成
   - 上传覆盖率到 Codecov

2. **构建** (仅 main 分支 push): 构建 Python 包并上传构建产物

3. **Docker** (仅 main 分支 push): 构建 Docker 镜像并验证

### 持续部署（CD）

发布流水线在推送版本标签（`v*`）时触发：

1. 构建 Python 包
2. 发布到 PyPI（通过 `PYPI_API_TOKEN` 密钥）
3. 创建 GitHub Release（自动生成 Release Notes）

### 发布流程

```bash
# 1. 更新版本号
# 2. 更新 CHANGELOG.md
# 3. 提交并打标签
git tag v3.1.1
git push origin v3.1.1

# CI/CD 会自动完成构建、发布和 Release 创建
```
