# Changelog

所有重要的变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [3.5.0] - 2026-05-12

### Added - 数据质量治理体系完善

#### 数据采集层增强
- **RateLimiter**: 全局限速器，令牌桶算法，支持多数据源独立限速（AKShare 5req/s, Tushare 1req/s）
- **HealthChecker**: 数据源健康检查器，定时主动探测，连续失败告警
- **IdempotentExecutor**: 幂等执行器，请求去重+结果缓存+装饰器支持

#### 缓存层增强
- **缓存穿透防护**: 空值缓存标记，防止不存在的数据反复查询数据源
- **缓存击穿防护**: 请求锁机制（get_with_lock），防止并发穿透
- **缓存雪崩防护**: TTL随机偏移（±10%），避免大量缓存同时过期

#### 分析层增强
- **DeterminismChecker**: 分析结果确定性验证器，快照测试+哈希比对
- **TraceContext**: 计算链路追踪，Trace ID贯穿全链路+Span嵌套

#### 输出层增强
- **DataMasker**: 数据脱敏器，支持基金代码/身份证/手机号/邮箱/金额脱敏
- **ReportValidator增强**: 模板变量类型验证+渲染输出质量验证+报告schema验证

#### 监控告警层增强
- **AlertNotifier**: 主动告警通知，支持CLI/Webhook/Email多渠道
- **QualityTrendAnalyzer**: 数据质量趋势分析，基于审计日志的异常检测
- **SLAMonitor**: SLA监控器，新鲜度/质量评分/响应时间SLA违规告警
- **MetricsExporter**: 质量指标可观测性导出器，支持Prometheus格式

#### 交易记录解析
- **TransactionParser**: Excel交易记录解析器，支持9种业务类型

#### 持仓计算
- **HoldingCalculator**: 持仓计算器，份额/成本/市值/盈亏计算

#### CI/CD
- 新增 `tests/quality/` 数据质量测试套件（35个测试用例）
- CI流水线增加数据质量测试步骤

### Changed
- DataCache版本升级至1.1（新增缓存防护机制）
- QualityGate集成AlertNotifier，质量检查失败自动告警
- DataSourceGateway集成RateLimiter，所有请求自动限速

## [3.4.0] - 2026-05-11

### Added - 智能推荐系统（Phase 4）

#### 用户画像模块 (user_profile.py)
- **RiskQuestionnaire**: 风险评估问卷，5道题目评估用户风险承受能力
- **StyleAnalyzer**: 投资风格分析器，基于交易行为和持仓历史分析投资风格
- **ProfileManager**: 用户画像管理器，支持创建、存储、查询用户画像
- **UserProfile**: 用户画像数据类，包含风险评估、投资目标、投资期限、偏好设置
- **RiskAssessment**: 风险评估结果，包含风险等级、得分、最大回撤容忍度
- **InvestmentPreferences**: 投资偏好设置，包含基金类型、行业、规模等偏好
- CLI命令: `fund ai profile show|create|assess`

#### 个性化推荐引擎 (recommender.py)
- **ContentBasedRecommender**: 基于内容的推荐器，基于基金特征匹配用户偏好
- **CollaborativeRecommender**: 协同过滤推荐器，基于相似用户行为推荐
- **HybridRecommender**: 混合推荐器，融合内容和协同过滤结果
- **FundRecommender**: 基金推荐主类，整合多种推荐策略
- **FundScore**: 基金评分数据类，包含综合得分和细分得分
- **RecommendationItem**: 推荐结果项，包含推荐理由和风险提示
- **RecommendationReport**: 推荐报告，包含完整推荐结果和摘要
- CLI命令: `fund ai recommend --fund 000001 --strategy hybrid`

#### 投资建议生成器 (advisor.py)
- **HoldingAnalyzer**: 持仓分析器，分析持仓结构、集中度、风险匹配度
- **RebalanceAdvisor**: 调仓建议器，生成调仓建议和目标配置
- **DCAAdvisor**: 定投建议器，生成定投方案和止盈止损策略
- **RiskAlerter**: 风险预警器，检测持仓风险并生成预警
- **InvestmentAdvisor**: 投资建议主类，整合持仓分析、调仓建议、定投方案、风险预警
- **AdviceItem**: 建议项数据类，包含建议类型、优先级、内容
- **RebalanceSuggestion**: 调仓建议数据类
- **DCASuggestion**: 定投建议数据类
- **InvestmentAdviceReport**: 投资建议报告
- CLI命令: `fund ai advise --funds 000001,000002 --type all`

### Changed
- AI模块 `__init__.py`: 导出新增的智能推荐系统类
- `ai_cmd.py`: 新增 profile/recommend/advise 三个CLI命令

### Tests
- 新增 45 个单元测试（Phase 4）
- 总测试数: 2144 passed

## [3.3.0] - 2026-05-11

### Added - AI 决策支持能力增强（Phase 1）

#### 智能选基助手 (fund_selector.py)
- **NeedParser**: 自然语言需求解析器，支持解析基金类型、收益目标、风险约束、规模偏好等
- **FundScorer**: 多因子评分引擎，支持收益/风险/夏普/规模/稳定性五因子评分
- **RecommendationGenerator**: 推荐理由生成器，自动生成个性化推荐理由和风险提示
- **FundSelector**: 智能选基主类，整合需求解析、筛选、评分、推荐全流程
- CLI命令: `fund ai select "稳健的股票型基金，年化收益10%以上"`

#### 投资组合诊断 (portfolio_doctor.py)
- **DiversificationAnalyzer**: 分散度分析器，计算HHI指数和有效持仓数量
- **ConcentrationAnalyzer**: 集中度分析器，分析Top1/Top3/Top5持仓集中度
- **CorrelationAnalyzer**: 相关性分析器，计算组合内资产相关性
- **RiskExposureAnalyzer**: 风险敞口分析器，分析各资产风险贡献
- **PortfolioDoctor**: 组合诊断主类，生成完整诊断报告
- CLI命令: `fund ai diagnose 000001,000002,000003 --weights 0.4,0.3,0.3`

#### 市场解读助手 (market_analyst.py)
- **SentimentAnalyzer**: 市场情绪分析器，计算恐慌贪婪指数
- **SectorRotationAnalyzer**: 行业轮动分析器，识别强势/弱势行业
- **HotspotTracker**: 热点追踪器，追踪市场热点主题
- **MarketAnalyst**: 市场解读主类，整合三大分析功能
- CLI命令: `fund ai market --type sentiment|rotation|hotspot`

#### AI Agent 工具扩展
- `smart_fund_selection`: 智能选基工具
- `diagnose_portfolio_health`: 组合诊断工具
- `analyze_market_sentiment`: 市场分析工具
- `get_fund_recommendation_by_style`: 风格推荐工具

### Added - 风险分析深度增强（Phase 2）

#### 压力测试模块 (stress_test.py)
- **HistoricalScenarioEngine**: 历史情景引擎，支持2008金融危机、2015股灾、2020疫情等情景
- **CustomScenarioEngine**: 自定义情景引擎，支持用户定义的压力情景
- **SensitivityAnalyzer**: 敏感性分析器，分析基金对各因子的敏感性
- **StressTester**: 压力测试主类，整合历史情景、自定义情景、敏感性分析
- CLI命令: `fund analyze stress-test 000001 --scenario "2008金融危机"`

#### 情景分析模块 (scenario_analysis.py)
- **BullBearAnalyzer**: 牛熊市分析器，分析基金在不同市场环境下的表现
- **RateSensitivityAnalyzer**: 利率敏感度分析器，分析债券基金对利率变动的敏感度
- **StyleRotationAnalyzer**: 风格轮动分析器，分析不同风格环境下的表现
- **ProbabilityWeightedAnalyzer**: 概率加权分析器，计算概率加权后的综合指标
- **ScenarioAnalyzer**: 情景分析主类，整合牛熊市、利率敏感度、风格轮动分析
- CLI命令: `fund analyze scenario-v2 000001 --type "股票型" --beta 1.2`

#### 风险预算模块 (risk_budget.py)
- **RiskContributionCalculator**: 风险贡献计算器，计算各资产的风险贡献
- **RiskConcentrationAnalyzer**: 风险集中度分析器，分析风险集中度
- **TailRiskAnalyzer**: 尾部风险分析器，分析VaR/CVaR贡献
- **RiskBudgetOptimizer**: 风险预算优化器，支持风险平价、最小方差等优化目标
- **RiskBudgetAnalyzer**: 风险预算分析主类，整合风险贡献、集中度、尾部风险分析
- CLI命令: `fund analyze risk-budget 000001,000002,000003 --optimize`

### Changed
- AI模块 `__init__.py`: 导出新增的智能决策支持类
- `ai_cmd.py`: 新增 select/diagnose/market 三个CLI命令
- `analyze_cmd.py`: 新增 stress-test/scenario-v2/risk-budget 三个CLI命令
- 工具总数: 86 → 90

### Added - 市场分析能力（Phase 3）

#### 资金流向分析 (money_flow.py)
- **FundFlowAnalyzer**: 基金申赎分析器，分析基金净申购/赎回趋势
- **SectorFlowAnalyzer**: 板块资金流向分析器，追踪主力/散户资金动向
- **NorthboundFlowAnalyzer**: 北向资金分析器，分析外资流入流出趋势
- **MoneyFlowAnalyzer**: 资金流向分析主类，整合三大分析功能
- CLI命令: `fund analyze money-flow --type fund|sector|northbound`

#### 行业轮动分析 (sector_rotation.py)
- **SectorPerformanceCalculator**: 行业表现计算器，多周期动量排名
- **RotationSignalDetector**: 轮动信号检测器，识别行业轮动对
- **SectorRotationAnalyzer**: 行业轮动分析主类，生成行业排名和轮动信号
- CLI命令: `fund analyze sector-rotation --period "近1月"`

#### 市场情绪指标 (market_sentiment.py)
- **FearGreedCalculator**: 恐慌贪婪指数计算器，6维度综合情绪指数
- **FundPositionEstimator**: 基金仓位估算器，估算基金整体仓位水平
- **MarketBreadthCalculator**: 市场宽度计算器，分析涨跌比和市场广度
- **SentimentAlertGenerator**: 情绪预警生成器，极端情绪自动预警
- **MarketSentimentAnalyzer**: 市场情绪分析主类，整合情绪、仓位、宽度分析
- CLI命令: `fund analyze sentiment`

### Changed
- `analysis/__init__.py`: 导出新增的市场分析类
- `analyze_cmd.py`: 新增 money-flow/sector-rotation/sentiment 三个CLI命令

### Tests
- 新增 55 个单元测试（Phase 3）
- 总测试数: 2132 passed

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
