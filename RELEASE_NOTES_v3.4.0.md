# Fund CLI v3.4.0 发布说明

## 版本信息
- **版本号**: 3.4.0
- **发布日期**: 2026-05-11
- **Python 要求**: >=3.10

## 新增功能

### Phase 4 - 智能推荐系统

#### 用户画像模块
- 风险评估问卷 (`RiskQuestionnaire`)
- 投资风格分析 (`StyleAnalyzer`)
- 用户画像管理 (`ProfileManager`)
- CLI 命令: `fund ai profile create/show/assess`

#### 个性化推荐引擎
- 基于内容的推荐 (`ContentBasedRecommender`)
- 协同过滤推荐 (`CollaborativeRecommender`)
- 混合推荐策略 (`HybridRecommender`)
- CLI 命令: `fund ai recommend`

#### 投资建议生成器
- 持仓分析 (`HoldingAnalyzer`)
- 调仓建议 (`RebalanceAdvisor`)
- 定投方案 (`DCAAdvisor`)
- 风险预警 (`RiskAlerter`)
- CLI 命令: `fund ai advise`

### Phase 1-3 功能回顾

#### AI 决策支持 (Phase 1)
- 智能选基: `fund ai select`
- 组合诊断: `fund ai diagnose`
- 市场解读: `fund ai market`

#### 风险分析 (Phase 2)
- 压力测试: `fund analyze stress-test`
- 情景分析: `fund analyze scenario-v2`
- 风险预算: `fund analyze risk-budget`

#### 市场分析 (Phase 3)
- 资金流向: `fund analyze money-flow`
- 行业轮动: `fund analyze sector-rotation`
- 市场情绪: `fund analyze sentiment`

## 测试统计
- 单元测试: 2144 个
- 集成测试: 33 个
- **总计: 2177 个测试全部通过**

## 安装升级

```bash
# 新安装
pip install fund-cli==3.4.0

# 升级
pip install --upgrade fund-cli==3.4.0
```

## 快速开始

```bash
# 创建用户画像
fund ai profile create --name "张三" --risk moderate --horizon long

# 获取个性化推荐
fund ai recommend --top 5

# 获取投资建议
fund ai advise --funds 000001,000002
```

## 文档
- 完整文档: README.md
- 更新日志: CHANGELOG.md

## 兼容性
- 完全向后兼容 v3.x
- 支持 Python 3.10/3.11/3.12

---

**发布状态**: ✅ 已准备好发布
