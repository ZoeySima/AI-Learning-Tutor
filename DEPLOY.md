# 推送 AI Learning Tutor 到 GitHub 的完整步骤

## 方案 A：使用 GitHub CLI（推荐，最简单）

### 1. 安装 GitHub CLI

访问 https://cli.github.com/ 下载安装，或者在 PowerShell 中运行：
```powershell
winget install --id GitHub.cli
```

### 2. 登录 GitHub
```bash
gh auth login
# 选择 GitHub.com
# 选择 HTTPS
# 选择 Login with a web browser
# 复制 one-time code，在浏览器中授权
```

### 3. 创建仓库并推送（一条命令搞定）
```bash
cd C:/Users/hzsima/ai-learning-tutor
gh repo create ai-learning-tutor --public --source=. --remote=origin --push
```

完成！仓库地址会自动显示。

---

## 方案 B：手动创建（不需要安装 gh）

### 1. 在 GitHub 网页创建仓库

访问 https://github.com/new

- Repository name: `ai-learning-tutor`
- Description: `AI-powered personalized learning tutor - 用 AI 重新定义学习`
- Public
- **不要**勾选 "Add a README file"（我们已经有了）
- **不要**勾选 "Add .gitignore"（我们已经有了）
- **不要**选择 License（我们已经有了）

点击 "Create repository"

### 2. 推送代码

复制 GitHub 给你的仓库 URL（类似 `https://github.com/你的用户名/ai-learning-tutor.git`），然后执行：

```bash
cd C:/Users/hzsima/ai-learning-tutor
git remote add origin https://github.com/你的用户名/ai-learning-tutor.git
git branch -M main
git push -u origin main
```

完成！

---

## 推送后的下一步

### 1. 添加 GitHub Topics（可选）

在仓库页面点击 "Add topics"，添加：
- `ai`
- `learning`
- `education`
- `claude`
- `anthropic`
- `python`
- `cli`

### 2. 编辑仓库描述（可选）

在仓库页面点击 ⚙️ Settings，在 "About" 部分填写：
- Description: `AI-powered personalized learning tutor - 用 AI 重新定义学习`
- Website: 留空或填你的博客
- Topics: 见上面

### 3. 创建 Release（可选）

```bash
cd C:/Users/hzsima/ai-learning-tutor
gh release create v0.1.0 --title "v0.1.0 - Initial Release" --notes "First public release of AI Learning Tutor

Features:
- 4-step learning methodology (Map → Learn → Quiz → Loop)
- CLI interface with session management
- Markdown export
- Based on Claude Opus 4.7"
```

或者在网页上：
- 点击 "Releases" → "Create a new release"
- Tag: `v0.1.0`
- Title: `v0.1.0 - Initial Release`
- Description: 复制上面的 notes

### 4. 发布到 PyPI（可选，让别人能 pip install）

```bash
cd C:/Users/hzsima/ai-learning-tutor

# 安装构建工具
pip install build twine

# 构建
python -m build

# 上传到 PyPI（需要先在 https://pypi.org 注册账号）
twine upload dist/*
```

---

## 验证安装

推送成功后，别人可以这样安装：

```bash
# 从 GitHub 安装
pip install git+https://github.com/你的用户名/ai-learning-tutor.git

# 如果发布到了 PyPI
pip install ai-learning-tutor
```

---

## 当前状态

✅ 代码已完成（1298 行）
✅ 本地 git 仓库已初始化
✅ 首次提交已完成
⏳ 等待推送到 GitHub

项目位置：C:/Users/hzsima/ai-learning-tutor
