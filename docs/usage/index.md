# Fund CLI v3.1 使用教程

欢迎使用 Fund CLI 专业基金分析工具。本教程涵盖 v3.1 版本全部 12 个子命令的使用方法，包含命令示例和预期输出说明。

## 命令速查表

| 子命令 | 说明 | 快速示例 |
|--------|------|----------|
| `fund filter` | 基金筛选 | `fund filter basic --type 股票型` |
| `fund analyze` | 基金分析 | `fund analyze metrics 000001` |
| `fund compare` | 基金对比 | `fund compare funds 000001 000002` |
| `fund holding` | 持仓分析 | `fund holding query 000001` |
| `fund manager` | 经理分析 | `fund manager info 000001` |
| `fund monitor` | 监控预警 | `fund monitor add 000001` |
| `fund optimize` | 组合优化 | `fund optimize max-sharpe 000001,000002` |
| `fund interactive` | 交互式模式 | `fund interactive` |
| `fund ai` | AI 分析 | `fund ai summarize 000001` |
| `fund report` | 报告生成 | `fund report generate -t single_fund -f 000001` |
| `fund data` | 数据管理 | `fund data stats` |
| `fund config` | 配置管理 | `fund config show` |

## 按场景推荐阅读路径

### 入门用户

建议按以下顺序阅读，快速上手核心功能：

1. [筛选与数据管理](filter-and-data.md) -- 学会查找基金
2. [基金分析](analysis.md) -- 查看基金详情和业绩
3. [基金对比](comparison.md) -- 横向比较多只基金
4. [报告生成](report-generation.md) -- 生成专业报告

### 专业分析师

建议重点关注以下模块：

1. [基金分析](analysis.md) -- 深入业绩指标和滚动分析
2. [持仓与经理分析](holding-and-manager.md) -- 持仓结构和经理能力
3. [AI 分析](ai-analysis.md) -- AI 辅助投资决策
4. [报告生成](report-generation.md) -- 批量生成多类型报告

### 量化研究员

建议重点关注以下模块：

1. [组合优化](optimization.md) -- 均值方差、夏普、风险平价
2. [基金对比](comparison.md) -- 滚动胜率和相关性分析
3. [AI 分析](ai-analysis.md) -- Agent 对话和组合分析
4. [监控预警](monitoring.md) -- 自动化监控和预警规则

## 全局命令

```bash
# 查看版本
fund --version

# 查看帮助
fund --help

# 环境诊断
fund doctor
```

预期输出（`fund doctor`）：

```
Fund CLI 环境诊断

  ✓ Python 版本: 3.10.x (>=3.10)

核心依赖:
  ✓ CLI框架 (typer): 0.x.x
  ✓ 终端美化 (rich): 13.x.x
  ✓ 数据处理 (pandas): 2.x.x
  ...
```

## 教程目录

- [筛选与数据管理](filter-and-data.md)
- [基金分析](analysis.md)
- [基金对比](comparison.md)
- [AI 分析](ai-analysis.md)
- [组合优化](optimization.md)
- [报告生成](report-generation.md)
- [持仓与经理分析](holding-and-manager.md)
- [监控预警](monitoring.md)
- [交互式模式](interactive.md)
