# 基金筛选与数据管理

本模块涵盖基金筛选（`fund filter`）和数据管理（`fund data`）两大功能，帮助你快速定位目标基金并管理本地数据缓存。

## 基础筛选

按基金类型、公司、规模等条件筛选基金。

```bash
# 按类型筛选股票型基金
fund filter basic --type 股票型
```

预期输出：

```
正在筛选基金...
┏━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ 代码   ┃ 名称         ┃ 类型   ┃ 规模   ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ 000001 │ 华夏成长混合 │ 混合型 │ 50.2亿 │
│ 000002 │ 华夏回报混合 │ 混合型 │ 30.1亿 │
│ ...    │ ...          │ ...    │ ...    │
└────────┴──────────────┴────────┴────────┘

共找到 20 只基金
```

## 组合筛选

多条件组合筛选，支持类型、公司、规模、关键词等参数。

```bash
# 筛选华夏基金旗下规模大于10亿的基金，返回50条
fund filter basic --company 华夏基金 --min-scale 10 --limit 50
```

```bash
# 关键词搜索
fund filter basic --keyword 成长 --limit 30
```

## 高级筛选

### 按费率筛选

```bash
# 筛选管理费不超过0.5%的基金
fund filter fee 0.5 --type 股票型
```

### 按业绩指标筛选

```bash
# 筛选年化收益>10%、最大回撤<20%、夏普>1.0的基金
fund filter performance --min-return 10 --max-drawdown 20 --min-sharpe 1.0
```

### 按评级筛选

```bash
# 筛选评级4星及以上的基金
fund filter rating 4
```

### 按经理筛选

```bash
# 查找某经理管理的所有基金
fund filter manager 张三
```

### 高级表达式筛选

```bash
# 使用自定义表达式筛选
fund filter advanced "return_1y > 15 and scale > 50"
```

## 数据导出

将筛选结果导出为 CSV 或 JSON 文件。

```bash
# 筛选并导出为 CSV
fund filter basic --type 股票型 -o result.csv
```

预期输出：

```
正在筛选基金...
...
共找到 20 只基金
已导出到: result.csv
```

```bash
# 使用专用导出命令，支持 JSON 格式
fund filter export funds_data.json --format json
```

## 筛选模板管理

保存常用筛选条件为模板，方便复用。

```bash
# 保存当前筛选模板
fund filter template save --name my_stock_filter

# 列出已保存的模板
fund filter template list
```

预期输出：

```
  - my_stock_filter
  - large_cap_value
```

```bash
# 加载模板
fund filter template load --name my_stock_filter

# 删除模板
fund filter template delete --name my_stock_filter
```

## 数据缓存管理

### 查看缓存统计

```bash
fund data stats
```

预期输出：

```
┏━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ 指标     ┃ 值         ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 缓存条目 │ 1,234      │
│ 缓存大小 │ 15.30 MB   │
│ 缓存目录 │ ~/.fund_cli│
└──────────┴────────────┘
```

### 清空缓存

```bash
fund data clear
```

预期输出：

```
缓存已清空
```

### 数据质量检查

```bash
fund data quality 000001
```

预期输出：

```
000001 数据质量报告：
  整体状态: good
  完整性评分: 95/100 (共500行, 缺失3个)
  准确性评分: 98/100 (异常值2个)
  时效性: up_to_date (最后更新: 2025-01-10)
```

### 增量更新

```bash
fund data update 000001
```

预期输出：

```
000001: 新增 5 条记录
```

### 批量下载

```bash
fund data batch-download 000001,000002,000003
```

预期输出：

```
正在批量下载...

批量下载完成
  总计: 3 只基金
  成功: 3
  失败: 0
```
