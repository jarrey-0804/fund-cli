# Fund CLI 发布检查清单

## 发布前检查

### 版本号
- [ ] `src/fund_cli/__init__.py` 中的 `__version__` 已更新
- [ ] `pyproject.toml` 中的 version 已更新
- [ ] `CHANGELOG.md` 已添加新版本记录

### 代码质量
- [ ] 运行 `ruff check src/ tests/` 无错误
- [ ] 运行 `ruff format --check src/ tests/` 无格式问题
- [ ] 运行 `bandit -r src/ -f txt` 无高危安全告警
- [ ] 运行 `pytest` 所有测试通过

### 文档
- [ ] `README.md` 已更新（如有新功能）
- [ ] API 文档已更新（如有接口变更）
- [ ] 使用指南已更新（如有操作变更）

### 依赖
- [ ] `requirements-lock.txt` 已重新生成
- [ ] 依赖兼容性已测试（Python 3.10/3.11/3.12）

## 发布步骤

1. 创建发布分支: `git checkout -b release/v{版本号}`
2. 提交变更: `git commit -am "release: v{版本号} - {描述}"`
3. 推送分支: `git push origin release/v{版本号}`
4. 创建 PR，等待 CI 通过
5. 合并到 main: `git checkout main && git merge release/v{版本号}`
6. 打标签: `git tag v{版本号}`
7. 推送标签: `git push origin v{版本号}`
8. 构建包: `python -m build`
9. 检查包: `twine check dist/*`
10. 发布到 PyPI: `twine upload dist/*`
11. 创建 GitHub Release

## 发布后验证

- [ ] PyPI 页面显示新版本
- [ ] `pip install fund-cli=={版本号}` 可正常安装
- [ ] `fund --version` 显示正确版本号
- [ ] 核心功能 (`fund diagnose`) 可正常运行
