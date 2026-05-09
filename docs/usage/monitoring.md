# 监控预警

`fund monitor` 命令提供基金监控池管理和净值变动预警功能，帮助你实时跟踪关注基金的净值变化。

## 监控池管理

### 添加基金到监控池

```bash
# 添加到默认分组
fund monitor add 000001
```

```bash
# 添加到指定分组
fund monitor add 000001 --group my_watchlist
```

预期输出：

```
已添加 000001 到 default 监控池
```

### 从监控池移除

```bash
fund monitor remove 000001
```

```bash
# 从指定分组移除
fund monitor remove 000001 --group my_watchlist
```

预期输出：

```
已从监控池移除 000001
```

### 列出监控池

```bash
# 列出所有监控基金
fund monitor list
```

```bash
# 列出指定分组的基金
fund monitor list --group my_watchlist
```

预期输出：

```
┏━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ 基金代码┃ 分组     ┃ 添加时间         ┃
┡━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ 000001 │ default  │ 2025-01-10 10:30 │
│ 000002 │ default  │ 2025-01-10 10:31 │
│ 000003 │ my_watch │ 2025-01-10 11:00 │
└────────┴──────────┴──────────────────┘

共 3 只基金
```

## 净值变动监控

对指定基金设置净值变动监控和预警阈值。

```bash
# 监控基金，日跌幅超过-2%时预警（默认阈值）
fund monitor watch 000001
```

```bash
# 自定义预警阈值（日跌幅超过-3%时预警）
fund monitor watch 000001 --threshold -3.0
```

```bash
# 设置更严格的阈值（日跌幅超过-1%时预警）
fund monitor watch 000001 --threshold -1.0
```

预期输出：

```
已开始监控 000001，阈值: -2.0%
```

## 检查预警

检查监控池中所有基金的净值变动，触发预警规则。

```bash
fund monitor check
```

预期输出（有预警时）：

```
正在检查 3 只基金...
┏━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ 基金代码┃ 日收益率 ┃ 阈值     ┃
┡━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ 000002 │ -2.50%   │ -2.00%   │
│ 000003 │ -3.10%   │ -2.00%   │
└────────┴──────────┴──────────┘

2 只基金触发预警
```

预期输出（无预警时）：

```
正在检查 3 只基金...
所有基金正常，无预警
```

## 查看预警规则

列出当前所有已设置的预警规则。

```bash
fund monitor alert
```

预期输出：

```
┏━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ 基金代码┃ 规则类型 ┃ 阈值     ┃
┡━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ 000001 │ nav_change│ -2.00%   │
│ 000002 │ nav_change│ -1.50%   │
│ 000003 │ nav_change│ -3.00%   │
└────────┴──────────┴──────────┘
```

## 典型使用流程

```bash
# 1. 添加关注基金到监控池
fund monitor add 000001
fund monitor add 000002 --group tech_funds
fund monitor add 000003 --group tech_funds

# 2. 设置预警规则
fund monitor watch 000001 --threshold -2.0
fund monitor watch 000002 --threshold -1.5

# 3. 查看监控池
fund monitor list

# 4. 检查预警
fund monitor check

# 5. 查看预警规则
fund monitor alert

# 6. 不再关注时移除
fund monitor remove 000003 --group tech_funds
```
