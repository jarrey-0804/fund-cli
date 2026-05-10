# PyPI Trusted Publishing 配置指南

本项目使用 PyPI Trusted Publishing（可信发布），无需存储 API Token。

## 配置步骤

### 1. 在 PyPI 上配置

1. 访问 https://pypi.org/manage/account/publishing/
2. 点击 "Add a new pending publisher"
3. 填写以下信息：
   - **PyPI Project Name**: `fund-cli`
   - **Owner**: `jarrey-0804`
   - **Repository name**: `fund-cli`
   - **Workflow name**: `release.yml`
   - **Environment name**: `pypi`

4. 点击 "Add"

### 2. 在 GitHub 上配置环境

1. 访问 https://github.com/jarrey-0804/fund-cli/settings/environments
2. 点击 "New environment"
3. 名称填写: `pypi`
4. 配置保护规则（可选）：
   - 添加 Required reviewers
   - 设置 Deployment branches

### 3. 触发发布

推送 tag 到 GitHub：

```bash
# 1. 确保代码已提交
git add .
git commit -m "Release v3.2.0"

# 2. 创建 tag
git tag v3.2.0

# 3. 推送 tag
git push origin v3.2.0
```

GitHub Actions 将自动：
1. 构建 wheel 和 sdist
2. 发布到 PyPI
3. 创建 GitHub Release

## 验证发布

```bash
# 等待几分钟后
pip install fund-cli==3.2.0
fund --version
```

## 故障排除

### 发布失败

检查 GitHub Actions 日志：
https://github.com/jarrey-0804/fund-cli/actions

### 常见问题

1. **Trusted Publishing 未配置**
   - 错误: `Token request failed`
   - 解决: 按照上述步骤配置 PyPI Trusted Publishing

2. **环境未配置**
   - 错误: `Environment pypi not found`
   - 解决: 在 GitHub Settings > Environments 中创建 `pypi` 环境

3. **权限不足**
   - 错误: `Resource not accessible by integration`
   - 解决: 检查 workflow 中的 `permissions: id-token: write`

## 参考文档

- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub Action: pypi-publish](https://github.com/marketplace/actions/pypi-publish)
