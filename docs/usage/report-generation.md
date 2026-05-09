# 报告生成

`fund report` 是 v3.1 的核心功能，支持多种报告类型和输出格式，可生成专业的基金分析报告。

## 报告类型

| 类型 | 说明 | 所需参数 |
|------|------|----------|
| `single_fund` | 单只基金分析报告 | `--fund` |
| `portfolio` | 投资组合报告 | `--funds` |
| `market_flow` | 市场资金流向报告 | 无 |
| `risk_control` | 风险控制报告 | 无 |

## 输出格式

| 格式 | 说明 | 文件扩展名 |
|------|------|-----------|
| `html` | 交互式网页报告（默认） | `.html` |
| `markdown` | Markdown 文本报告 | `.md` |
| `pdf` | PDF 文档报告 | `.pdf` |

## 生成单只基金报告

```bash
# 生成 HTML 格式报告（默认）
fund report generate --type single_fund --fund 000001
```

预期输出：

```
报告已生成: report_single_fund_000001.html
```

```bash
# 指定输出格式为 Markdown
fund report generate --type single_fund --fund 000001 --format markdown
```

```bash
# 指定输出格式为 PDF
fund report generate --type single_fund --fund 000001 --format pdf
```

```bash
# 指定输出路径
fund report generate --type single_fund --fund 000001 --format html --output my_report.html
```

## 生成投资组合报告

```bash
# 生成组合报告
fund report generate --type portfolio --funds 000001,000002,000003
```

```bash
# 指定格式和输出路径
fund report generate --type portfolio --funds 000001,000002 --format pdf --output portfolio_report.pdf
```

预期输出：

```
报告已生成: report_portfolio_000001.html
```

## 生成市场资金流向报告

```bash
fund report generate --type market_flow --format html
```

预期输出：

```
报告已生成: report_market_flow_portfolio.html
```

## 生成风险控制报告

```bash
fund report generate --type risk_control --format html
```

预期输出：

```
报告已生成: report_risk_control_portfolio.html
```

## 查看可用模板

```bash
fund report list-templates
```

预期输出：

```
可用模板:
  - single_fund
  - portfolio
  - market_flow
  - risk_control
  - base
```

## 使用自定义模板

通过 `--template` 参数指定自定义模板路径，覆盖默认模板。

```bash
fund report generate --type single_fund --fund 000001 --template ./my_template.html
```

## 命令参数汇总

```bash
fund report generate \
  --type single_fund \       # 报告类型
  --fund 000001 \            # 基金代码（单基金报告）
  --funds 000001,000002 \    # 多基金代码（组合报告）
  --format html \            # 输出格式
  --output report.html \     # 输出路径（可选）
  --template ./custom.html   # 自定义模板（可选）
```

## 报告内容说明

### 单只基金报告（single_fund）

包含基金基本信息、净值走势图、业绩指标汇总、风险分析等模块。HTML 格式支持交互式图表。

### 投资组合报告（portfolio）

包含组合内各基金的权重分布、收益贡献、相关性矩阵和整体风险指标。

### 市场资金流向报告（market_flow）

展示市场整体资金流向、行业配置变化和热点板块分析。

### 风险控制报告（risk_control）

包含组合风险敞口分析、VaR 计算、压力测试结果和风险限额监控。
