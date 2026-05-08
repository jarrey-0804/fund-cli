# Fund CLI V2.0 发布操作指南

**发布版本**: 2.0.0  
**发布日期**: 2026-05-08  
**PyPI账号**: Jarrey0804

---

## ✅ 发布前准备已完成

- [x] 版本号验证: 2.0.0
- [x] 测试通过: 296/296
- [x] 代码质量检查: Black + Ruff 通过
- [x] 构建成功: fund_cli-2.0.0.tar.gz + fund_cli-2.0.0-py3-none-any.whl
- [x] CHANGELOG.md 已创建
- [x] CONTRIBUTING.md 已创建

---

## 🔐 PyPI 发布配置

### 方法1: 使用 API Token (推荐)

**步骤1**: 登录 PyPI 创建 API Token
1. 访问 https://pypi.org/manage/account/token/
2. 点击 "Add API token"
3. Token name: `fund-cli-release`
4. Scope: 选择 "Entire account" 或指定项目
5. 复制生成的 token (格式: `pypi-xxxxxxxx`)

**步骤2**: 配置本地环境

```bash
# 方法A: 使用 .pypirc 文件
cat > ~/.pypirc << 'EOF'
[pypi]
username = __token__
password = pypi-您的token这里

[testpypi]
username = __token__
password = pypi-您的token这里
EOF

chmod 600 ~/.pypirc
```

```bash
# 方法B: 使用环境变量
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-您的token这里
```

### 方法2: 使用用户名密码

```bash
# 配置 .pypirc
cat > ~/.pypirc << 'EOF'
[pypi]
username = Jarrey0804
password = 您的密码
EOF

chmod 600 ~/.pypirc
```

---

## 📤 发布步骤

### 步骤1: 进入项目目录

```bash
cd /workspace/fund-cli
```

### 步骤2: 验证构建产物

```bash
ls -la dist/
# 应该包含:
# - fund_cli-2.0.0.tar.gz
# - fund_cli-2.0.0-py3-none-any.whl

twine check dist/*
# 预期: PASSED
```

### 步骤3: 测试发布到 TestPyPI (可选但推荐)

```bash
# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 验证测试安装
pip install --index-url https://test.pypi.org/simple/ fund-cli==2.0.0
fund --version
```

### 步骤4: 正式发布到 PyPI

```bash
# 上传到 PyPI
twine upload dist/*

# 或使用交互模式
twine upload --sign dist/*
```

### 步骤5: 验证发布

```bash
# 从 PyPI 安装
pip install fund-cli==2.0.0

# 验证版本
fund --version
# 预期输出: 2.0.0

# 验证核心功能
fund --help
fund ai --help
```

---

## 🏷️ GitHub Release 创建

### 步骤1: 提交并推送代码

```bash
# 添加所有文件
git add .

# 提交
git commit -m "chore: release v2.0.0

- Add AI analysis module with OpenAI/Qwen support
- Add holding analysis module
- Add fund manager analysis module
- Add portfolio optimization enhancements
- Add performance attribution module
- Add monitoring and alerts module
- Update documentation and changelog"

# 推送
git push origin main
```

### 步骤2: 创建 Git 标签

```bash
# 创建标签
git tag -a v2.0.0 -m "Release version 2.0.0"

# 推送标签
git push origin v2.0.0
```

### 步骤3: 创建 GitHub Release

访问: https://github.com/your-org/fund-cli/releases/new

**Release 信息**:

```markdown
## Fund CLI V2.0.0 正式发布

### 🎉 核心亮点

- **🤖 AI辅助分析**: 集成多LLM提供商，支持智能基金分析
- **📊 持仓分析**: 持仓穿透、行业分布、风格分析
- **⚖️ 组合优化**: 均值-方差、最大夏普、风险平价策略
- **👤 基金经理**: 经理业绩追踪、稳定性评估
- **🔔 实时监控**: 净值变动监控、预警通知
- **💻 交互式模式**: REPL风格交互体验

### 📦 安装

```bash
pip install fund-cli==2.0.0
```

### 📚 文档

- [安装指南](docs/installation.md)
- [使用教程](docs/usage/tutorial.md)
- [API文档](docs/api/reference.md)
- [CHANGELOG](CHANGELOG.md)

### 📝 主要变更

**新增功能**:
- AI分析模块（summarize, compare, advice, risk, insight, portfolio）
- 持仓分析模块（query, industry, concentration, changes, style）
- 基金经理模块（info, performance, stability）
- 组合优化增强（mean-variance, max-sharpe, risk-parity, frontier, backtest）
- 业绩归因模块
- 监控预警模块

**改进**:
- 数据层架构重构
- CLI界面优化
- 缓存机制优化

**修复**:
- 内存占用问题
- 时区处理问题
```

---

## ✅ 发布后验证清单

- [ ] PyPI 页面可访问: https://pypi.org/project/fund-cli/2.0.0/
- [ ] README 正确渲染
- [ ] 可从 PyPI 安装: `pip install fund-cli==2.0.0`
- [ ] 版本号正确: `fund --version` 显示 2.0.0
- [ ] GitHub Release 已创建
- [ ] Git 标签已推送

---

## 🆘 故障排除

### 问题1: 上传失败 "HTTPError: 403 Forbidden"

**原因**: 认证失败

**解决**:
```bash
# 检查 .pypirc 权限
chmod 600 ~/.pypirc

# 或使用环境变量
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-您的token
```

### 问题2: "File already exists"

**原因**: 该版本已存在

**解决**:
- PyPI 不允许覆盖已发布的版本
- 需要增加版本号重新构建

### 问题3: "Invalid or non-existent authentication"

**原因**: Token 无效

**解决**:
- 在 PyPI 重新生成 API Token
- 确保使用 `__token__` 作为用户名

---

## 📞 支持

如有问题，请联系:
- GitHub Issues: https://github.com/your-org/fund-cli/issues
- Email: your-email@example.com

---

**发布日期**: 2026-05-08  
**发布版本**: 2.0.0
