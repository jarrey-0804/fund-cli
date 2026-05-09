# 安全策略

## 安全策略

Fund CLI 团队高度重视项目和用户的安全。我们致力于及时响应和修复安全漏洞，确保用户数据和 API 密钥的安全。

## 漏洞报告流程

如果您发现安全漏洞，请**不要**通过公开的 GitHub Issue 报告。请按照以下流程报告：

1. **通过 GitHub Security Advisories 报告**
   - 访问 [Security Advisories](https://github.com/jarrey-0804/fund-cli/security/advisories/new)
   - 选择 "Report a vulnerability"
   - 填写漏洞详情，包括：
     - 漏洞描述
     - 影响范围
     - 复现步骤
     - 可能的修复建议（可选）

2. **确认与响应**
   - 团队将在 **48 小时内** 确认收到报告
   - 我们将在 **7 个工作日内** 提供初步评估
   - 修复方案的时间表将根据漏洞严重程度确定

3. **公开披露**
   - 在修复版本发布后，我们将公开披露漏洞详情
   - 如果您同意，我们将在安全公告中致谢您的贡献

## 支持版本

| 版本 | 支持状态 |
|------|----------|
| v3.x (最新) | 完全支持，接收安全更新 |
| v2.x | 仅接收关键安全修复 |
| v1.x | 不再支持 |

## API Key 保护

Fund CLI 使用多种 API 密钥（AKShare、Tushare、Wind、OpenAI 等），请遵循以下安全实践：

- **不要**将 API 密钥硬编码在源码中
- **不要**将包含密钥的配置文件提交到版本控制
- 使用环境变量或 `.env` 文件存储密钥（参考 `.env.example`）
- `.env` 文件已包含在 `.gitignore` 中
- 在 CI/CD 环境中使用 GitHub Secrets 管理密钥

```bash
# 推荐方式：使用环境变量
export TUSHARE_TOKEN="your_token_here"
export OPENAI_API_KEY="your_key_here"

# 或使用 .env 文件（不提交到 Git）
cp .env.example .env
# 编辑 .env 填入实际密钥
```

## 安全最佳实践

- 保持依赖更新：定期运行 `pip install --upgrade -e ".[dev]"` 更新依赖
- 使用虚拟环境隔离项目依赖
- 审查 `pyproject.toml` 中的依赖声明，确保没有已知漏洞的版本
- 定期运行 `make lint` 进行代码安全检查
