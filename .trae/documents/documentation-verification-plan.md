# 文档验证与修复计划

## 摘要

文档改进计划（P0-P5）已全部执行完毕，当前处于验证阶段。本计划旨在完成最后的验证工作，修复发现的 3 个问题，确保文档站点可以正确构建。

## 当前状态分析

### 已完成的工作
- **P0**: mkdocs.yml 配置、占位符 URL 替换
- **P1**: 首页重写、安装指南扩展、10 个使用教程
- **P2**: API 参考文档（7 个页面，含 mkdocstrings 自动 API 生成）
- **P3**: 开发指南扩展（架构图、新数据源指南、CI/CD 流程）
- **P4**: SECURITY.md、CODE_OF_CONDUCT.md、GitHub Issue/PR 模板
- **P5**: README.md 增强（v3.0 特性、Docker）、CONTRIBUTING.md 增强

### 发现的问题

| 优先级 | 问题 | 文件 | 影响 |
|--------|------|------|------|
| **高** | `docs/contributing.md` 不存在，但 mkdocs.yml nav 引用了它 | mkdocs.yml 第 99 行 | `mkdocs build --strict` 会失败 |
| **低** | CODE_OF_CONDUCT.md 第 37 行 `[在此处插入联系邮箱]` 未填写 | CODE_OF_CONDUCT.md | 不影响构建，但不够专业 |
| **低** | `docs/usage/tutorial.md` 存在但未被 mkdocs.yml 引用 | docs/usage/tutorial.md | 孤立文件，不影响构建 |

## 修复步骤

### 步骤 1: 创建 docs/contributing.md
- **文件**: `/workspace/fund-cli/docs/contributing.md`
- **内容**: 基于 MkDocs 格式创建贡献指南页面，内容从根目录 `CONTRIBUTING.md` 提炼，适配文档站风格
- **原因**: mkdocs.yml nav 第 99 行引用了 `contributing.md`，缺失会导致构建失败

### 步骤 2: 修复 CODE_OF_CONDUCT.md 占位符
- **文件**: `/workspace/fund-cli/CODE_OF_CONDUCT.md` 第 37 行
- **修改**: `[在此处插入联系邮箱]` → `fund-cli-security@googlegroups.com`（使用 Google Groups 通用项目邮箱格式）
- **原因**: 消除最后一个占位符，提升专业度

### 步骤 3: 处理 docs/usage/tutorial.md 孤立文件
- **文件**: `/workspace/fund-cli/docs/usage/tutorial.md`
- **操作**: 删除该文件（内容与 `usage/index.md` 重复）
- **原因**: 避免混淆，保持文档目录整洁

### 步骤 4: 运行 mkdocs build --strict 验证
- **命令**: `cd /workspace/fund-cli && mkdocs build --strict`
- **预期**: 构建成功，无错误或警告
- **原因**: 确认文档站点可以正确构建

### 步骤 5: 最终占位符检查
- **搜索**: 在所有 .md 和 .yml 文件中搜索 `TODO`、`FIXME`、`CHANGE_ME`、`REPLACE`、`在此处`、`placeholder` 等关键词
- **预期**: 无匹配结果
- **原因**: 确保无残留占位符

## 验证步骤
1. `mkdocs build --strict` 构建成功（0 错误 0 警告）
2. 全文搜索无残留占位符
3. mkdocs.yml nav 结构与实际文件完全一致
