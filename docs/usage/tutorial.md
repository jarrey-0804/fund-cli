# 使用教程

## 基金筛选

```bash
# 按类型筛选
fund filter basic --type 股票型

# 按公司筛选
fund filter basic --company 华夏基金

# 组合筛选
fund filter basic --type 股票型 --min-scale 10 --limit 50

# 导出结果
fund filter basic --type 股票型 -o result.csv
```

## 基金分析

```bash
# 查看基金信息
fund analyze info 000001

# 查看净值历史
fund analyze nav 000001 --start 2023-01-01 --end 2023-12-31

# 分析业绩指标
fund analyze metrics 000001

# 带基准对比分析
fund analyze metrics 000001 -b 000300
```

## 基金对比

```bash
# 多基金对比
fund compare funds 000001 000002 000003

# 指定分析周期
fund compare funds 000001 000002 --period 3y
```

## 配置管理

```bash
# 查看当前配置
fund config
```

## 数据管理

```bash
# 查看缓存统计
fund data stats

# 清空缓存
fund data clear
```
