# Fund CLI 项目指令

## 项目概述
Fund CLI 是一个专业的基金分析命令行工具，使用 Python 3.10+，基于 Typer 框架。
版本：3.2.0 | 协议：MIT

## 常用命令

- 安装依赖：`pip install -e ".[dev]"`
- 运行测试：`pytest tests/ -q`
- 运行测试（含覆盖率）：`pytest tests/ --cov=src/fund_cli --cov-report=term-missing`
- 代码检查：`ruff check src/`
- 代码格式化：`ruff format src/`
- 类型检查：`mypy src/ --ignore-missing-imports`
- 全部检查：`ruff check src/ && ruff format src/ --check && mypy src/ --ignore-missing-imports && pytest tests/ -q`
- 构建发布：`python -m hatch build`
- 本地安装验证：`pip install dist/fund_cli-*.whl`

## 代码风格

- 使用 Google 风格 docstring（中文）
- 行长度 100 字符
- 使用类型注解
- 函数不超过 100 行
- 使用绝对导入
- 中文注释和文档字符串

## 项目架构

```
src/fund_cli/
├── cli.py              # CLI 入口，Typer app
├── config.py           # Pydantic 配置管理
├── ai/                 # AI 模块（LangChain Agent）
│   ├── agent.py        # Agent 定义
│   ├── analyzer.py     # AI 分析器
│   ├── tools.py        # LangChain @tool 工具
│   ├── memory.py       # 对话历史管理
│   └── providers.py    # LLM 提供商
├── analysis/           # 分析模块
│   ├── performance.py  # PerformanceAnalyzer
│   ├── risk.py         # RiskAnalyzer
│   ├── holding.py      # HoldingAnalyzer
│   └── attribution.py  # 归因分析
├── commands/           # Typer 命令
│   ├── analyze_cmd.py  # fund analyze
│   ├── compare_cmd.py  # fund compare
│   ├── optimize_cmd.py # fund optimize
│   ├── holding_cmd.py  # fund holding
│   ├── ai_cmd.py       # fund ai
│   └── report_cmd.py   # fund report
├── core/               # 核心模块
│   ├── data_manager.py # DataManager 数据管理
│   ├── monitor.py      # FundMonitor 监控
│   ├── quality_gate.py # QualityGate 质量门禁
│   ├── calc_validator.py    # CalcValidator 计算验证
│   ├── cross_validator.py   # CrossValidator 交叉验证
│   ├── ai_validator.py      # AIOutputValidator AI验证
│   ├── report_validator.py  # ReportValidator 报告验证
│   ├── audit_logger.py      # AuditLogger 审计日志
│   └── reporters/      # 报告生成器
├── data/               # 数据层
│   ├── adapters/       # 数据适配器（akshare/tushare/wind）
│   ├── base.py         # 适配器基类
│   ├── cache.py        # 缓存管理
│   └── normalizer.py   # 数据标准化
└── utils/              # 工具函数
```

## 测试规范

- 测试目录镜像 src/ 结构：tests/unit/test_core/, tests/unit/test_commands/
- 使用 pytest + unittest.mock
- AAA 模式：Arrange-Act-Assert
- 测试文件命名：test_<module>.py
- 测试类命名：Test<Feature>
- 优先运行单个测试文件：`pytest tests/unit/test_core/test_data_manager.py -v`
- 不修改测试来通过实现，修改实现来通过测试

## 数据质量治理（v3.2.0 核心特性）

五层架构：
1. **数据采集层**：Gateway 路由 + 熔断器/重试/降级
2. **数据标准化管道**：Pydantic 验证 + 重复检测
3. **质量检查引擎**：8 项 Expectation 自动化检查
4. **计算验证层**：CalcValidator 12 项指标验证
5. **输出合规层**：ReportValidator + 免责声明

IMPORTANT：所有分析操作必须通过 QualityGate 检查，不合格数据不得进入计算流程。

## Git 规范

- Conventional Commits：feat/fix/docs/refactor/test/chore
- 分支命名：feature/xxx、fix/xxx
- 不直接推送到 main，使用 PR

## 注意事项

- AI 模块依赖 LangChain，修改 tools.py 时注意 @tool 装饰器
- 数据适配器层有熔断机制，测试时需要 mock 网络请求
- 报告生成器支持 html/pdf/docx/pptx/markdown 格式
- 配置通过 .env 文件或环境变量，参考 .env.example
