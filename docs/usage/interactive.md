# 交互式模式

`fund interactive` 命令启动交互式 REPL（Read-Eval-Print Loop）模式，无需反复输入 `fund` 前缀，适合连续执行多个分析操作。

## 进入交互式模式

```bash
fund interactive
```

预期输出：

```
╭──────────────────────────────────────────╮
│ Fund CLI 交互式模式                      │
│ 输入命令（如 info 000001）或 help 查看帮助│
│ 输入 exit 或 quit 退出                   │
╰──────────────────────────────────────────╯
fund>
```

## REPL 命令

在交互式模式中，可以直接输入子命令和参数，无需 `fund` 前缀。

```bash
fund> info 000001
```

预期输出：

```
╭──────────────────────────────────╮
│         华夏成长混合              │
├──────────┬───────────────────────┤
│ 基金代码 │ 000001                │
│ 基金名称 │ 华夏成长混合           │
│ ...      │ ...                   │
╰──────────┴───────────────────────╯
```

```bash
fund> analyze metrics 000001 -b 000300
```

```bash
fund> compare funds 000001 000002 --period 1y
```

```bash
fund> filter basic --type 股票型 --limit 10
```

```bash
fund> holding query 000001
```

```bash
fund> manager info 000001
```

```bash
fund> data stats
```

```bash
fund> config show
```

## 自动补全

交互式模式基于 `prompt_toolkit` 实现命令自动补全，输入命令前几个字母后按 `Tab` 键即可触发。

```bash
fund> in<Tab>
# 自动补全为: info

fund> an<Tab>
# 自动补全为: analyze

fund> fil<Tab>
# 自动补全为: filter
```

支持的补全命令列表：

- `info` -- 查看基金信息
- `filter` -- 基金筛选
- `analyze` -- 基金分析
- `compare` -- 基金对比
- `optimize` -- 组合优化
- `monitor` -- 监控预警
- `holding` -- 持仓分析
- `manager` -- 经理分析
- `data` -- 数据管理
- `config` -- 配置管理

## 查看帮助

```bash
fund> help
```

预期输出：

```
可用命令: info, filter, analyze, compare, optimize,
          monitor, holding, manager, data, config
输入 exit 或 quit 退出
```

## 退出

以下三种方式均可退出交互式模式：

```bash
fund> exit
```

```bash
fund> quit
```

或直接按 `Ctrl+C` / `Ctrl+D`。

预期输出：

```
再见！
```

## 依赖说明

交互式模式需要安装 `prompt_toolkit` 库。如果未安装，启动时会提示安装。

```bash
pip install prompt_toolkit
```

如果未安装 `prompt_toolkit`，将无法进入交互式模式并提示：

```
需要安装 prompt_toolkit: pip install prompt_toolkit
```

## 典型使用场景

交互式模式适合以下场景：

1. **连续分析多只基金**：无需每次输入 `fund` 前缀
2. **探索性研究**：快速切换不同命令和参数
3. **演示和教学**：实时展示分析过程

示例会话：

```bash
fund interactive
fund> filter basic --type 股票型 --min-scale 10 -l 5
fund> analyze info 000001
fund> analyze metrics 000001 -b 000300
fund> holding query 000001
fund> manager info 000001
fund> compare funds 000001 000002 000003
fund> exit
再见！
```
