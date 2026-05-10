# Changelog

所有重要的变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [3.2.0] - 2026-05-10

### Added - 数据质量风险治理体系（核心特性）
- 五层数据质量治理架构
  - Layer 1 数据采集层质量门禁: DataManager路由改用Gateway，激活熔断器/重试/降级
  - Layer 2 数据标准化管道: Normalizer集成Pydantic模型验证、重复检测、净值范围校验
  - Layer 3 数据质量检查引擎: Expectation风格8项自动化检查（非空/数据量/列完整/净值非空/净值范围/收益率范围/日期唯一/时效性）
  - Layer 4 计算验证层: 12项指标合理性边界验证、交叉验证（PerformanceAnalyzer vs RiskAnalyzer）
  - Layer 5 输出合规层: 报告完整性验证、免责声明检查、质量徽章
- 质量门禁 (QualityGate): 分析入口强制执行数据质量检查，不达标拦截
- 计算结果验证器 (CalcValidator): Sharpe/回撤/波动率/Beta/VaR等12项指标合理性检查
- 交叉验证器 (CrossValidator): 多引擎计算结果交叉比对
- AI输出验证器 (AIOutputValidator): AI生成文本与源数据一致性校验、矛盾表述检测
- 报告验证器 (ReportValidator): 必需字段检查、模板数据完整性、免责声明检查
- 审计日志 (AuditLogger): 质量检查/分析操作/报告生成日志，支持合规审计和查询
- 合规风控报告生成器 (RiskControlReporter): 风险概览/集中度分析/合规检查数据填充
- 质量配置 (QualityConfig): 质量门禁阈值、异常检测参数、审计日志配置
- Monitor扩展: 支持回撤/波动率/夏普比率监控规则
- 71个新增单元测试（覆盖全部6个新模块）
- 总测试数: 2001 passed

### Changed
- DataManager: 关键方法(get_fund_info/nav/holdings/manager/benchmark)路由改用Gateway+Normalizer
- DataSourceGateway: 激活请求级内存缓存(5min TTL)，修复hash碰撞(MD5)，print→logging
- DataCache: 版本控制(CACHE_VERSION)、1GB容量限制、增强统计信息
- Normalizer: Pydantic模型验证集成、重复行检测、净值范围校验(0<nav<=10000)
- validators.py: 新增validate_nav_value/validate_daily_return/validate_data_min_rows/validate_date_strict
- decorators.py: retry增加指数退避+抖动，新增validate_input装饰器
- report_cmd.py: 修复空数据问题，集成ReportValidator，实现真实数据获取和分析
- analyze_cmd.py: 集成质量门禁+交叉验证+计算验证，显示质量评分

### Fixed
- DataManager第107行日志变量bug（主数据源切换日志显示错误）
- report_cmd.py传入空metrics={}的严重问题
- 风控报告模板(risk_control)无后端数据填充
- DataQualityChecker孤岛模块（从未被自动调用）
- Pydantic模型与数据流脱节（11个模型零调用）
- validators.py/decorators.py死代码（7个工具零调用）

## [3.1.0] - 2026-05-09

### Added
- 多数据源架构（v3.1核心特性）
  - TushareAdapter: P0级别18个核心方法，适配Tushare 2025.11 API变更
  - AKShareAdapter: AKShare数据源适配器
  - WindAdapter: Wind金融终端适配器（占位实现）
  - DataSourceGateway: 数据源网关，提供熔断器、降级、重试机制
  - DataNormalizer: 跨数据源数据标准化（字段映射、日期、代码、数值）
  - DataSourceAdapterMixin: 120+抽象方法占位实现
- 报告引擎增强
  - Reporter基类扩展: render_to_template, export_pdf, export_docx, export_pptx
  - TemplateEngine: Jinja2模板引擎，自定义过滤器(percentage/format_number/color_class)
  - 4类报告模板: 单基金研究、投资组合、市场资金流向、合规风控
  - PdfReporter: WeasyPrint HTML转PDF
  - DocxReporter: python-docx Word报告
  - PptxReporter: python-pptx PPT报告
- AI分析增强
  - AIAnalyzer: 基金/组合智能分析
  - RuleBasedBackend: 规则引擎（无需API）
  - OpenAIBackend: OpenAI API后端
  - AnalysisResult: 摘要、风险提示、投资建议、亮点、风险点
- CLI命令扩展
  - fund report: 报告生成命令
  - fund list-templates: 列出可用模板

### Changed
- DataManager集成DataSourceGateway，支持多源自动降级
- 改进代码质量: ruff lint + mypy类型检查全部通过
- 新增35个端到端集成测试

### Fixed
- 修复TushareAdapter抽象方法实现问题
- 修复DataNormalizer类型转换问题

## [2.0.1] - 2026-05-08

### Fixed
- 修复PyPI文档链接显示为空的问题
- 将README.md中的文档链接改为GitHub绝对链接
- 在README.md中直接包含安装指南、使用教程、API文档、开发指南内容

## [2.0.0] - 2026-05-08

### Added
- AI辅助分析功能（V2.0核心特性）
  - 支持OpenAI、阿里云Qwen等LLM提供商
  - 基金摘要生成、对比分析、投资建议、风险评估
  - 可配置API参数，切换方便
- 持仓分析模块
  - 持仓查询、行业分布分析
  - 重仓股分析、持仓集中度(HHI)
  - 持仓变化追踪、风格分析(九宫格)
- 基金经理分析
  - 经理信息查询、业绩统计
  - 稳定性评估
- 组合优化功能
  - 均值-方差优化、最大夏普比率优化
  - 风险平价优化、有效前沿计算
  - 组合回测功能
- 业绩归因模块
  - Brinson归因模型
  - 收益分解、风险归因
- 监控预警功能
  - 监控池管理、净值变动监控
  - 预警规则设置、通知功能
- 交互式模式
  - REPL风格交互界面
  - 命令自动补全

### Changed
- 重构数据层架构，支持多数据源适配器
- 优化缓存机制，提升数据获取性能
- 改进CLI界面，使用Rich库增强输出效果
- 增强基金筛选功能，支持高级表达式
- 增强基金分析功能，支持滚动窗口、月度分布、情景分析

### Fixed
- 修复大数据集下的内存占用问题
- 修复时区处理不一致问题

## [1.0.0] - 2024-XX-XX

### Added
- 初始版本发布
- 基础基金筛选功能
- 业绩分析功能（收益率、夏普比率、最大回撤等）
- 基金对比功能
- 数据管理功能（多数据源、缓存、导出）
- 系统配置功能
