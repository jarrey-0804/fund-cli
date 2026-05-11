# Claude Code 深度研究报告 - Fund CLI 迭代指南

> 本报告基于 Claude Code 官方文档与实践经验整理，旨在为 Fund CLI 项目的下一轮迭代提供 AI 辅助开发的系统性指导。

---

## 一、Claude Code 概述

### 1.1 什么是 Claude Code

Claude Code 是 Anthropic 推出的**智能体编码环境（Agentic Coding Environment）**，它不仅仅是一个聊天机器人，而是一个能够自主理解代码库、执行操作、编写代码的 AI 编程助手。Claude Code 运行在终端中，拥有对文件系统的读写权限，能够执行 shell 命令，并配备了丰富的内置工具链。

### 1.2 与普通 Claude API 的核心区别

| 特性 | Claude API（聊天） | Claude Code（智能体） |
|------|-------------------|---------------------|
| 工具调用 | 需要手动定义和实现 | 内置文件读写、搜索、终端执行等工具 |
| 上下文管理 | 单轮/多轮对话 | 自主循环：思考-行动-观察-反思 |
| 权限控制 | 无 | 六种权限模式，细粒度文件访问控制 |
| IDE 集成 | 无 | 原生支持 VS Code 和 JetBrains |
| 代码理解 | 需要手动粘贴代码 | 自动索引和搜索整个代码库 |
| 错误修复 | 需要手动反馈 | 自动检测构建/测试失败并修复 |

### 1.3 核心交互模式

**CLI REPL 模式（默认）**
```bash
# 启动交互式会话
claude

# 在指定目录启动
claude --project-dir /path/to/project

# 使用特定模型
claude --model claude-sonnet-4-20250514
```

**一次性模式（Non-interactive / Headless）**
```bash
# 单条指令执行
claude -p "运行测试并修复失败的用例"

# 管道输入
cat error.log | claude -p "分析这个错误并给出修复方案"

# 在 CI/CD 中使用
claude -p "审查最近的提交" --output-format json
```

**IDE 集成模式**
- **VS Code**：安装 Anthropic 官方扩展，在侧边栏或终端中使用
- **JetBrains**：安装 Claude Code 插件，支持 IntelliJ 全家桶

### 1.4 关键斜杠命令

| 命令 | 功能 | 使用场景 |
|------|------|---------|
| `/init` | 自动分析项目并生成 CLAUDE.md | 项目初始化、新成员加入 |
| `/compact` | 压缩对话上下文，保留关键信息 | 长对话上下文接近上限时 |
| `/model` | 切换模型（sonnet/opus/hybrids） | 不同任务需要不同能力时 |
| `/review` | 对当前变更进行代码审查 | 提交 PR 前的最终检查 |
| `/memory` | 查看/编辑 CLAUDE.md 记忆文件 | 调整项目指令和偏好 |
| `/cost` | 查看当前会话的 token 消耗和费用 | 成本监控和优化 |
| `/clear` | 清除对话历史 | 开始全新任务时 |
| `/config` | 查看/修改 Claude Code 配置 | 调整权限模式等设置 |
| `/doctor` | 检查 Claude Code 安装和配置 | 排查环境问题 |
| `/help` | 查看所有可用命令 | 命令参考 |

---

## 二、AI 推理与构建

### 2.1 Extended Thinking 扩展思考模式

Claude Code 支持 Extended Thinking（扩展思考）模式，在处理复杂问题时，Claude 会在给出最终答案前进行深度的内部推理。这对以下场景特别有效：

- **复杂架构设计**：多模块交互、设计模式选择
- **疑难 Bug 定位**：需要追踪多层调用链的问题
- **大规模重构**：需要理解全局影响范围的代码变更

启用方式：
```bash
# 通过模型切换启用（Opus 模型默认启用）
/model claude-opus-4-20250514

# Hybrid 模式：简单任务用 Sonnet，复杂任务自动升级到 Opus
/model hybrid
```

**Fund CLI 实践建议**：在处理数据质量治理、多适配器架构等复杂模块时，建议使用 Opus 或 Hybrid 模型以获得更深入的推理能力。

### 2.2 多文件上下文理解

Claude Code 拥有 **200K token 的上下文窗口**，能够同时理解大量代码文件。其工作方式：

1. **自动索引**：启动时扫描项目结构，建立文件索引
2. **按需读取**：根据任务需求，自动读取相关文件
3. **语义搜索**：使用 Grep/Glob 工具进行代码搜索，而非盲目读取
4. **上下文压缩**：通过 `/compact` 命令压缩历史，为新任务腾出空间

**上下文管理最佳实践**：
- 一个会话聚焦一个任务，避免上下文污染
- 完成复杂任务后使用 `/clear` 开始新会话
- 使用 `/compact` 在长会话中保持上下文效率
- 对于 Fund CLI 这种中型项目，Claude Code 可以在一次会话中理解完整的模块关系

### 2.3 自动构建工作流

Claude Code 能够自主执行完整的构建-测试-修复循环：

```
1. 读取项目配置（pyproject.toml, Makefile, CLAUDE.md）
       ↓
2. 运行构建命令（pip install -e ".[dev]"）
       ↓
3. 执行测试（pytest tests/ -q）
       ↓
4. 分析失败输出（如果有）
       ↓
5. 定位问题源文件
       ↓
6. 编辑修复
       ↓
7. 重新运行测试验证
       ↓
8. 循环直到所有测试通过
```

**Fund CLI 实践建议**：在 CLAUDE.md 中明确记录构建和测试命令（已完成），Claude Code 会自动遵循这些指令执行构建验证。

### 2.4 测试生成能力

Claude Code 能够分析现有测试的风格和模式，生成风格一致的测试用例：

```
1. 分析现有测试文件（tests/ 目录）
       ↓
2. 识别测试风格（AAA 模式、命名规范、fixture 使用）
       ↓
3. 理解被测模块的公共接口和边界条件
       ↓
4. 生成匹配风格的测试用例
       ↓
5. 运行测试验证通过
```

**Fund CLI 实践建议**：Claude Code 已经能够识别项目使用 pytest + unittest.mock + AAA 模式。新增模块时，可以要求 Claude Code 先分析 `tests/` 目录的现有测试风格，再生成新测试。

---

## 三、测试驱动开发（TDD）

### 3.1 Red-Green-Refactor 四步流程

Claude Code 原生支持 TDD 工作流，能够严格按照以下步骤执行：

```
Step 1: RED（红）    → 编写一个失败的测试，定义期望行为
Step 2: GREEN（绿）  → 编写最小实现使测试通过
Step 3: REFACTOR（重构）→ 优化代码结构，确保测试仍然通过
Step 4: REPEAT（重复）→ 选择下一个行为，回到 Step 1
```

### 3.2 显式 TDD 指令模式

在 Claude Code 中，可以通过明确的指令驱动 TDD 流程：

```
请使用 TDD 方式实现 XXX 功能：
1. 先分析需求，列出需要测试的行为清单
2. 逐个编写失败的测试用例
3. 编写最小实现使测试通过
4. 重构优化
5. 确保所有测试通过后再进行下一步

不要跳过任何步骤，不要先写实现再补测试。
```

**关键原则**：
- **先写测试，再写实现**：这是 TDD 的核心，Claude Code 会严格遵守
- **一个测试驱动一个行为**：每次只关注一个功能点
- **测试即文档**：测试用例本身就是最好的行为说明

### 3.3 覆盖率提升策略

**行为驱动测试（Behavior-Driven Testing）**
```python
# 不是测试实现细节，而是测试行为
def test_calculate_annual_return_should_handle_negative_returns():
    """当基金年度收益为负时，应正确计算并返回负值"""
    analyzer = PerformanceAnalyzer()
    result = analyzer.calculate_annual_return(
        nav_start=1.5, nav_end=1.2, years=1
    )
    assert result == pytest.approx(-0.2, rel=1e-4)
```

**边界条件测试（Boundary Testing）**
```python
# 测试边界值和极端情况
@pytest.mark.parametrize("nav", [0.0, -1.0, float('inf'), float('nan')])
def test_performance_analyzer_handles_invalid_nav(nav):
    """应正确处理无效的净值输入"""
    analyzer = PerformanceAnalyzer()
    with pytest.raises(ValueError):
        analyzer.calculate_annual_return(nav_start=nav, nav_end=1.5, years=1)
```

**属性基测试（Property-Based Testing）**
```python
# 使用 hypothesis 进行属性基测试
from hypothesis import given, strategies as st

@given(
    nav_start=st.floats(min_value=0.01, max_value=100),
    nav_end=st.floats(min_value=0.01, max_value=100),
    years=st.floats(min_value=0.1, max_value=30)
)
def test_annual_return_is_always_finite(nav_start, nav_end, years):
    """对于任意合理的输入，年化收益率应始终为有限值"""
    analyzer = PerformanceAnalyzer()
    result = analyzer.calculate_annual_return(nav_start, nav_end, years)
    assert np.isfinite(result)
```

### 3.4 Hypothesis 属性基测试集成

Hypothesis 是 Python 生态中强大的属性基测试库，与 pytest 无缝集成：

```bash
# 安装
pip install hypothesis
```

```python
from hypothesis import given, strategies as st, settings
from hypothesis.provisional import URLs

class TestDataManagerProperties:
    """DataManager 的属性基测试"""

    @given(data=st.lists(st.floats(min_value=0.01), min_size=2))
    @settings(max_examples=100)
    def test_normalized_data_should_preserve_ranking(self, data):
        """标准化后的数据应保持原始排名"""
        manager = DataManager()
        normalized = manager.normalize(data)
        original_order = sorted(data, reverse=True)
        normalized_order = sorted(normalized, reverse=True)
        # 排名应该一致
        for orig, norm in zip(original_order, normalized_order):
            assert (orig > 0 and norm > 0) or (orig <= 0 and norm <= 0)
```

**Fund CLI 实践建议**：
- 对 `PerformanceAnalyzer`、`RiskAnalyzer` 等计算密集型模块优先引入 Hypothesis
- 对数据标准化管道（`normalizer.py`）进行属性基测试，确保数据变换的正确性
- 对 `CalcValidator` 的验证规则进行属性基测试，确保验证逻辑的完备性

---

## 四、修复与审查

### 4.1 Bug 自动修复流程

Claude Code 拥有系统化的 Bug 修复能力，遵循以下流程：

```
1. 获取错误信息
   ├── 读取错误日志 / 测试输出 / 用户报告
   └── 理解错误类型：运行时异常 / 断言失败 / 类型错误

2. 搜索相关源文件
   ├── 使用 Grep 搜索错误消息、函数名、类名
   └── 使用 Glob 查找相关模块文件

3. 阅读和理解逻辑
   ├── 读取相关源文件的完整上下文
   └── 理解调用链和数据流

4. 编辑修复
   ├── 定位根因（root cause），而非只修表象
   └── 编写最小化修复，避免引入新问题

5. 验证修复
   ├── 运行相关测试
   └── 确认修复有效且无回归
```

**实用指令示例**：
```
pytest tests/unit/test_core/test_data_manager.py -v 报错了，
请分析失败原因并修复。修复后运行全部测试确保无回归。
```

### 4.2 Checkpoint 机制

Claude Code 在每次文件编辑前会自动创建快照（Checkpoint），这是一个非常实用的安全机制：

- **自动快照**：每次 `Edit`、`Write` 操作前自动保存当前状态
- **快速回退**：按 `Esc` 两次即可回退到上一个快照
- **多次回退**：可以连续回退多个编辑步骤
- **安全探索**：鼓励大胆尝试，因为随时可以回退

**实践建议**：
- 让 Claude Code 大胆重构，不用担心改坏——随时可以回退
- 在探索性任务（如架构调整）中充分利用 Checkpoint 机制
- 如果 Claude Code 的修改方向不对，直接按 `Esc` 两次回退

### 4.3 /review 命令代码审查

`/review` 命令会对当前的代码变更（相对于 git HEAD）进行全面审查：

```bash
# 在 Claude Code REPL 中执行
/review
```

审查维度包括：
- **代码质量**：命名规范、代码结构、可读性
- **潜在 Bug**：空指针、边界条件、异常处理
- **安全风险**：注入攻击、敏感信息泄露
- **性能问题**：不必要的计算、内存泄漏
- **测试覆盖**：是否有足够的测试保护
- **风格一致性**：是否符合项目编码规范

### 4.4 GitHub PR 自动审查

通过在 PR 评论中 `@claude`，可以触发 Claude Code 对 PR 进行自动审查：

```yaml
# .github/workflows/claude-review.yml
name: Claude Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          model: claude-sonnet-4-20250514
          direct_prompt: |
            审查这个 PR 的代码变更，关注：
            1. 是否符合项目的编码规范（Google docstring, 100字符行宽）
            2. 是否有潜在的 Bug 或安全问题
            3. 测试覆盖是否充分
            4. 是否遵循了数据质量治理的五层架构
```

---

## 五、CLAUDE.md 配置

### 5.1 四层记忆体系

Claude Code 采用分层记忆架构，从全局到局部逐层细化：

```
┌─────────────────────────────────────────────┐
│  第一层：企业策略（Enterprise）               │
│  路径：~/.claude/CLAUDE.md                   │
│  作用域：所有项目，所有用户                    │
│  内容：公司级编码标准、安全策略、合规要求       │
├─────────────────────────────────────────────┤
│  第二层：项目指令（Project）                   │
│  路径：<project-root>/CLAUDE.md              │
│  作用域：当前项目的所有用户                    │
│  内容：项目架构、构建命令、编码规范             │
├─────────────────────────────────────────────┤
│  第三层：用户偏好（User Preferences）          │
│  路径：<project-root>/CLAUDE.local.md        │
│  作用域：当前项目的当前用户                    │
│  内容：个人编辑器设置、常用命令别名             │
├─────────────────────────────────────────────┤
│  第四层：本地配置（Local）                     │
│  路径：<project-root>/.claude/settings.json  │
│  作用域：当前项目的当前用户、当前机器           │
│  内容：API Key、本地路径、环境特定配置          │
└─────────────────────────────────────────────┘
```

### 5.2 @path/to/file 导入语法

CLAUDE.md 支持通过 `@` 语法导入外部文件内容，避免重复维护：

```markdown
# Fund CLI 项目指令

## 编码规范
@docs/coding-standards.md

## 架构文档
@docs/architecture.md

## Git 工作流
@CONTRIBUTING.md
```

**注意事项**：
- 导入的文件内容会被内联展开，计入 CLAUDE.md 的总长度
- 建议只导入关键文档，避免上下文膨胀
- 导入路径支持相对路径（相对于项目根目录）

### 5.3 .claude/rules/ 规则目录

`.claude/rules/` 目录允许创建按文件路径限定作用域的规则文件：

```
.claude/rules/
├── general.md              # 通用规则（对所有文件生效）
├── python.md               # Python 文件规则（对 *.py 生效）
├── testing.md              # 测试文件规则（对 tests/**/*.py 生效）
└── data-adapters.md        # 数据适配器规则（对 src/fund_cli/data/** 生效）
```

规则文件格式示例（`.claude/rules/testing.md`）：
```markdown
---
description: 测试文件编写规则
globs: tests/**/*.py
---

# 测试编写规则

- 使用 AAA（Arrange-Act-Assert）模式
- Mock 外部依赖（网络请求、数据库）
- 测试函数命名：test_<行为描述>
- 每个测试只验证一个行为
- 使用 pytest.mark.parametrize 进行参数化测试
```

**YAML frontmatter 支持的字段**：
- `description`：规则描述
- `globs`：文件匹配模式（支持 glob 语法）
- `alwaysApply`：是否始终应用（忽略 globs 匹配）

### 5.4 CLAUDE.md 最佳实践

**控制在 200 行以内**
- 过长的 CLAUDE.md 会消耗宝贵的上下文窗口
- 使用 `@` 导入语法将详细文档放在外部文件中
- 使用 `.claude/rules/` 将特定规则分散管理

**具体可验证**
```markdown
# 好的写法
- 函数不超过 100 行
- 使用 Google 风格 docstring（中文）
- 行长度 100 字符

# 不好的写法
- 代码要写得简洁
- 注释要清楚
```

**结构化组织**
```markdown
# 项目名称 - CLAUDE.md

## 项目概述（3-5 行）
## 常用命令（构建/测试/部署）
## 代码风格（具体规则列表）
## 项目架构（目录结构说明）
## 测试规范（测试策略和约定）
## 注意事项（特殊约束和陷阱）
```

**Fund CLI 当前状态**：项目已有完善的 CLAUDE.md（约 100 行），涵盖了项目概述、常用命令、代码风格、架构、测试规范等核心内容。建议在下一轮迭代中：
1. 创建 `.claude/rules/` 目录，按模块拆分规则
2. 将数据质量治理的详细规则移入 `.claude/rules/data-quality.md`
3. 将 AI 模块的开发规范移入 `.claude/rules/ai-module.md`

---

## 六、Hooks 系统

### 6.1 四种事件类型

Claude Code 的 Hooks 系统允许在特定事件发生时自动执行自定义脚本：

| 事件 | 触发时机 | 典型用途 |
|------|---------|---------|
| `PreToolUse` | 工具执行前 | 拦截危险操作、自动格式化、权限检查 |
| `PostToolUse` | 工具执行后 | 日志记录、自动 lint、通知 |
| `Notification` | 需要用户注意时 | 发送桌面通知、声音提醒 |
| `Stop` | Claude 完成任务时 | 运行最终测试、生成报告 |

### 6.2 退出码控制

Hooks 脚本通过退出码控制 Claude Code 的行为：

| 退出码 | 含义 | Claude Code 行为 |
|--------|------|-----------------|
| `0` | 成功 | 继续执行 |
| `2` | 阻止 | 阻止当前操作，将脚本 stdout 作为反馈发送给 Claude |
| 其他 | 忽略 | 继续执行（脚本输出不发送给 Claude） |

### 6.3 JSON 输出控制

Hooks 脚本可以通过 stdout 输出 JSON 来精细控制行为：

```json
{"decision": "approve"}     // 批准操作
{"decision": "block"}       // 阻止操作
{"decision": "undefined"}   // 不做决定，交给用户确认
```

### 6.4 配置方式

Hooks 在 `.claude/settings.json` 中配置：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "ruff format --stdin-filename $FILE_PATH",
        "timeout": 5000
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "ruff check --stdin-filename $FILE_PATH",
        "timeout": 5000
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "command": "pytest tests/ -q --tb=no",
        "timeout": 30000
      }
    ]
  }
}
```

### 6.5 实用示例

**自动格式化（PreToolUse Hook）**
```bash
#!/bin/bash
# .claude/hooks/auto-format.sh
# 在 Claude 写入 Python 文件前自动格式化

FILE_PATH="$CLAUDE_FILE_PATH"
if [[ "$FILE_PATH" == *.py ]]; then
    ruff format "$FILE_PATH" 2>/dev/null
fi
exit 0
```

**日志记录（PostToolUse Hook）**
```bash
#!/bin/bash
# .claude/hooks/log-edits.sh
# 记录所有文件编辑操作

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
TOOL="$CLAUDE_TOOL_NAME"
FILE="$CLAUDE_FILE_PATH"
echo "[$TIMESTAMP] $TOOL: $FILE" >> .claude/edit-log.txt
exit 0
```

**保护生产文件（PreToolUse Hook）**
```bash
#!/bin/bash
# .claude/hooks/protect-prod.sh
# 阻止修改生产配置文件

FILE_PATH="$CLAUDE_FILE_PATH"
PROTECTED_FILES=("prod_config.py" "production.env" "deploy.yaml")

for pf in "${PROTECTED_FILES[@]}"; do
    if [[ "$FILE_PATH" == *"$pf"* ]]; then
        echo "错误：不允许修改生产文件 $FILE_PATH"
        exit 2  # 阻止操作
    fi
done
exit 0
```

**Fund CLI 实践建议**：
1. 配置 PreToolUse Hook：在写入 `.py` 文件后自动运行 `ruff format`
2. 配置 PostToolUse Hook：在编辑后自动运行 `ruff check`，发现问题反馈给 Claude 修复
3. 配置 Stop Hook：Claude 完成任务后自动运行快速测试验证

---

## 七、子代理（Subagent）

### 7.1 核心概念

子代理（Subagent）是 Claude Code 中独立的 AI 代理实例，具有以下特点：

- **独立上下文窗口**：子代理有自己的对话历史，不会污染主对话
- **任务隔离**：每个子代理专注于一个特定任务
- **结果汇总**：子代理完成后将结果返回给主代理
- **并行执行**：多个子代理可以同时运行（最多 10 个并发）

### 7.2 配置方式

子代理配置文件放在 `.claude/agents/` 目录下，使用 Markdown + YAML frontmatter 格式：

```markdown
---
name: test-runner
description: 运行测试并分析失败原因
model: claude-sonnet-4-20250514
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# 测试运行器

你是一个专业的测试工程师。你的任务是：

1. 运行指定的测试命令
2. 分析测试失败的原因
3. 定位问题源文件
4. 提供修复建议（但不直接修改代码）

## 输出格式

请按以下格式输出结果：

### 测试结果摘要
- 总测试数：X
- 通过：Y
- 失败：Z

### 失败分析
对于每个失败的测试：
- 测试名称
- 失败原因
- 相关源文件
- 建议修复方案
```

### 7.3 推荐子代理配置

**code-reviewer（代码审查员）**
```markdown
---
name: code-reviewer
description: 审查代码变更，关注质量、安全和规范
model: claude-sonnet-4-20250514
---

# 代码审查员

审查代码变更时，请关注以下维度：

1. **编码规范**：是否符合 Google docstring、100 字符行宽
2. **类型安全**：是否有缺失的类型注解
3. **异常处理**：是否有适当的 try/except 和错误消息
4. **数据质量**：是否通过 QualityGate 检查
5. **测试覆盖**：是否有对应的测试用例
6. **安全性**：是否有注入风险或敏感信息泄露
```

**debugger（调试专家）**
```markdown
---
name: debugger
description: 分析和定位 Bug 根因
model: claude-opus-4-20250514
---

# 调试专家

你的调试流程：

1. 复现问题：理解错误信息和复现步骤
2. 搜索线索：在代码库中搜索相关代码
3. 追踪调用链：从入口到出错点完整追踪
4. 定位根因：区分表象和根因
5. 提出修复：给出最小化修复方案
```

**test-runner（测试运行器）**
```markdown
---
name: test-runner
description: 运行测试并分析结果
model: claude-sonnet-4-20250514
---

# 测试运行器

## 职责
1. 运行指定的 pytest 命令
2. 分析测试输出
3. 对失败测试进行根因分析
4. 生成测试报告摘要

## 注意事项
- 使用 `pytest tests/ -q --tb=short` 快速运行
- 失败时使用 `--tb=long` 获取详细堆栈
- 关注 flaky test（不稳定测试）
```

**data-analyst（数据分析师）**
```markdown
---
name: data-analyst
description: 分析基金数据质量和计算结果
model: claude-sonnet-4-20250514
---

# 数据分析师

## 职责
1. 验证数据采集质量
2. 检查数据标准化管道
3. 验证计算结果正确性
4. 生成数据质量报告

## 关注点
- 数据完整性：是否有缺失值、异常值
- 计算准确性：年化收益、波动率、夏普比等指标
- 一致性：不同数据源的结果是否一致
```

### 7.4 并行执行

Claude Code 可以并行调度多个子代理，大幅提升效率：

```
主代理：分析 Issue，拆分任务
  ├── 子代理 1：审查代码变更
  ├── 子代理 2：运行单元测试
  ├── 子代理 3：运行集成测试
  └── 子代理 4：检查代码覆盖率
       ↓
主代理：汇总所有子代理结果，生成最终报告
```

**Fund CLI 实践建议**：
- 创建 `.claude/agents/` 目录，配置上述推荐子代理
- 在处理复杂 Issue 时，使用子代理并行执行审查和测试
- 对于数据质量分析任务，使用专用的 data-analyst 子代理

---

## 八、GitHub 集成

### 8.1 Claude Code GitHub Action

Anthropic 提供了官方 GitHub Action，可以在 CI/CD 流水线中使用 Claude Code：

```yaml
# .github/workflows/claude.yml
name: Claude Code
on:
  issue_comment:
    types: [created]
  pull_request:
    types: [opened, synchronize, reopened]
  issues:
    types: [opened, labeled]

jobs:
  claude:
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request' && contains(github.event.pull_request.body, '@claude')) ||
      (github.event_name == 'issues' && contains(github.event.issue.body, '@claude'))
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: anthropics/claude-code-action@v1
        with:
          model: claude-sonnet-4-20250514
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          direct_prompt: |
            你是 Fund CLI 项目的维护者。
            请根据 Issue/PR 的描述进行处理。
            遵循 CLAUDE.md 中的项目规范。
            完成后运行测试确保所有检查通过。
```

### 8.2 @claude 触发自动处理

在 GitHub 中，通过 `@claude` 触发自动处理：

**Issue 自动处理**
```markdown
# Bug: 数据适配器在超时后未正确降级

@claude 请修复这个问题。复现步骤：
1. 配置 akshare 适配器
2. 设置超时时间为 1 秒
3. 请求一个需要较长时间的数据
4. 观察是否正确降级到缓存数据
```

**PR 自动审查**
```markdown
@claude 请审查这个 PR，关注：
1. 数据质量治理五层架构是否被正确遵循
2. 测试覆盖率是否足够
3. 是否有潜在的回归风险
```

### 8.3 CI 失败自动修复工作流

```yaml
# .github/workflows/auto-fix.yml
name: Auto Fix CI Failures
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]

jobs:
  auto-fix:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.workflow_run.head_branch }}
          fetch-depth: 0

      - uses: anthropics/claude-code-action@v1
        with:
          model: claude-sonnet-4-20250514
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          direct_prompt: |
            CI 测试失败了。请：
            1. 运行测试找出失败的用例
            2. 分析失败原因
            3. 修复代码使测试通过
            4. 运行全部测试确保无回归
            5. 提交修复并推送
```

### 8.4 云服务提供商支持

Claude Code GitHub Action 支持多种后端：

```yaml
# 使用 AWS Bedrock
- uses: anthropics/claude-code-action@v1
  with:
    model: anthropic.claude-sonnet-4-20250514-v1:0
    api_provider: bedrock
    aws_region: us-east-1

# 使用 Google Vertex AI
- uses: anthropics/claude-code-action@v1
  with:
    model: claude-sonnet-4@20250514
    api_provider: vertex
    vertex_project: my-project
    vertex_region: us-east5
```

**Fund CLI 实践建议**：
1. 在 `.github/workflows/` 中配置 Claude Code Action
2. 在 `ISSUE_TEMPLATE/bug_report.md` 中添加 `@claude` 提示
3. 配置 CI 失败自动修复工作流，减少人工干预
4. 在 PR 模板中添加 `@claude` 审查提示

---

## 九、权限与安全

### 9.1 六种权限模式

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `default` | 写入/编辑需确认，读取自动批准 | 日常开发（推荐） |
| `acceptEdits` | 自动批准编辑，shell 命令需确认 | 信任度较高的任务 |
| `plan` | 只读模式，不执行任何修改 | 架构探索、代码审查 |
| `auto` | 自动批准所有操作 | CI/CD 环境、高度信任 |
| `dontAsk` | 自动批准所有操作（含危险操作） | 仅限本地沙箱环境 |
| `bypassPermissions` | 跳过所有权限检查 | 极度危险，仅限调试 |

### 9.2 权限模式切换

在 Claude Code REPL 中，使用 `Shift+Tab` 循环切换权限模式：

```
当前模式: default
按 Shift+Tab 切换到: acceptEdits → plan → auto → dontAsk → default
```

**实践建议**：
- **日常开发**：使用 `default` 模式，对文件修改保持审查
- **代码审查**：使用 `plan` 模式，只读分析不修改
- **批量重构**：使用 `acceptEdits` 模式，自动批准编辑
- **CI/CD**：使用 `auto` 模式，全自动执行

### 9.3 文件夹访问限制

Claude Code 有严格的文件系统访问限制：

- **不能访问上级目录**：Claude Code 只能访问项目根目录及其子目录
- **不能访问其他项目**：每个 Claude Code 实例被限制在其项目范围内
- **敏感文件保护**：通过 Hooks 可以额外保护特定文件

```
/workspace/fund-cli/          ← 项目根目录（可访问）
├── src/                      ← 可访问
├── tests/                    ← 可访问
├── .env                      ← 可访问（建议通过 Hooks 保护）
└── ../other-project/         ← 不可访问
```

### 9.4 防提示注入保护

Claude Code 内置了多层提示注入防护：

1. **CLAUDE.md 优先级**：项目指令优先于用户输入中的指令
2. **工具输出标记**：工具返回的内容被标记为不可信，不会被当作指令执行
3. **文件内容隔离**：读取的文件内容不会覆盖系统指令
4. **权限确认**：关键操作需要用户确认，防止自动执行恶意指令

**安全最佳实践**：
- 不要在 CLAUDE.md 中存储 API Key 或密码
- 使用 `.claude/settings.local.json`（不提交到 Git）存储敏感配置
- 使用 `.gitignore` 排除 `.claude/settings.local.json`
- 对生产环境配置文件添加 Hooks 保护

---

## 十、Fund CLI 迭代建议

### 10.1 立即可执行的改进

**1. 优化 CLAUDE.md 配置（已完成基础版）**

当前项目的 CLAUDE.md 已经覆盖了核心内容。建议进一步优化：

```
fund-cli/
├── CLAUDE.md                    # 保持精简（<150 行）
└── .claude/
    ├── settings.json            # Hooks 和权限配置
    ├── rules/
    │   ├── python-style.md      # Python 编码规范
    │   ├── testing.md           # 测试规范（globs: tests/**/*.py）
    │   ├── data-quality.md      # 数据质量规则（globs: src/fund_cli/data/**）
    │   └── ai-module.md         # AI 模块规范（globs: src/fund_cli/ai/**）
    └── agents/
        ├── test-runner.md       # 测试运行子代理
        ├── code-reviewer.md     # 代码审查子代理
        └── data-analyst.md      # 数据分析子代理
```

**2. 配置 Hooks 实现自动格式化和检查**

在 `.claude/settings.json` 中配置：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "if echo \"$CLAUDE_FILE_PATH\" | grep -q '\\.py$'; then ruff format \"$CLAUDE_FILE_PATH\" && ruff check \"$CLAUDE_FILE_PATH\" --fix; fi",
        "timeout": 10000
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "command": "cd /workspace/fund-cli && pytest tests/ -q --tb=no 2>&1 | tail -5",
        "timeout": 60000
      }
    ]
  }
}
```

### 10.2 中期改进计划

**3. 创建专用子代理**

为 Fund CLI 的核心模块创建专用子代理，提升任务处理效率：

- **test-runner**：自动运行测试、分析失败、生成报告
- **code-reviewer**：按项目规范审查代码变更
- **data-analyst**：验证数据质量和计算结果
- **refactor-agent**：执行大规模重构，确保测试通过

**4. 配置 GitHub Actions 实现 @claude 自动处理**

- 在 Issue 模板中引导用户使用 `@claude`
- 配置 PR 自动审查工作流
- 配置 CI 失败自动修复工作流
- 设置 `CLAUDE_CODE_OAUTH_TOKEN` 密钥

**5. 使用 Plan 模式进行架构探索**

在重大架构变更前，使用 Plan 模式进行无副作用的探索：

```bash
# 切换到 Plan 模式（Shift+Tab）
claude> 请分析将数据适配器层从同步改为异步的可行性，
        评估影响范围，给出迁移方案。不要修改任何文件。
```

### 10.3 长期改进方向

**6. 建立 TDD 工作流**

在项目开发中全面推行 TDD：

```
新功能开发流程：
1. 使用 Claude Code 分析需求
2. Claude Code 编写失败测试（Red）
3. Claude Code 编写最小实现（Green）
4. Claude Code 重构优化（Refactor）
5. 运行全部测试确保无回归
6. 使用 /review 进行最终审查
```

**7. 属性基测试覆盖**

为核心计算模块引入 Hypothesis 属性基测试：

```bash
# 安装依赖
pip install hypothesis

# 优先覆盖的模块
tests/unit/test_analysis/test_performance.py    # PerformanceAnalyzer
tests/unit/test_analysis/test_risk.py           # RiskAnalyzer
tests/unit/test_core/test_calc_validator.py     # CalcValidator
tests/unit/test_data/test_normalizer.py         # 数据标准化
```

**8. 持续优化 CLAUDE.md**

随着项目演进，持续更新 CLAUDE.md：

- 新增模块时更新架构说明
- 发现新的常见问题时添加注意事项
- 根据实际使用体验调整指令表述
- 定期使用 `/memory` 命令审查和更新记忆

### 10.4 推荐的迭代路线图

```
Phase 1（立即执行）：
├── 创建 .claude/rules/ 规则目录
├── 配置 .claude/settings.json（Hooks）
└── 优化 CLAUDE.md（精简到 <150 行）

Phase 2（1-2 周内）：
├── 创建 .claude/agents/ 子代理配置
├── 引入 Hypothesis 属性基测试
└── 建立 TDD 工作流模板

Phase 3（1 个月内）：
├── 配置 GitHub Actions（@claude 自动处理）
├── 建立 CI 失败自动修复流水线
└── 完善 Plan 模式架构探索流程

Phase 4（持续优化）：
├── 根据使用反馈调整子代理配置
├── 扩展 Hooks 覆盖更多自动化场景
└── 持续优化 CLAUDE.md 和规则文件
```

---

> **文档版本**：v1.0
> **创建日期**：2026-05-10
> **适用项目**：Fund CLI v3.2.0+
> **Claude Code 版本**：基于 Claude Code 最新文档整理
