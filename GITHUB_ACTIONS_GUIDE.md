# GitHub Actions 使用指南

> 本文档详细介绍如何在真实场景下配置和使用 GitHub Actions 进行 API 自动化测试

---

## 一、前置准备

### 1.1 需要准备
| 项目 | 说明 |
|-----|------|
| GitHub 账号 | 免费账号即可，私有仓库每月 2000 分钟免费额度 |
| Git 本地安装 | 用于推送代码 |
| 项目代码 | 你的自动化测试项目 |

### 1.2 初始化 Git 仓库

```bash
# 进入项目目录
cd /path/to/your/project

# 初始化 Git（如果还没有）
git init

# 添加所有文件
git add .

# 首次提交
git commit -m "Initial commit: API automation test framework"
```

### 1.3 推送到 GitHub

**Step 1**: 在 GitHub 创建新仓库
1. 登录 GitHub → 点击右上角 **+** → **New repository**
2. 填写仓库名称（如 `woniu-api-test`）
3. 选择 Private 或 Public
4. **不要勾选** "Add a README file"（因为本地已有文件）
5. 点击 **Create repository**

**Step 2**: 关联远程仓库并推送
```bash
# 添加远程仓库
git remote add origin https://github.com/你的用户名/woniu-api-test.git

# 推送代码
git branch -M main
git push -u origin main
```

---

## 二、配置文件详解

### 2.1 文件位置
```
项目根目录/
└── .github/
    └── workflows/
        └── api-test.yml    # GitHub Actions 配置文件
```

### 2.2 配置详解

```yaml
# ==================== 工作流名称 ====================
name: API Tests  # 在 GitHub Actions 页面显示的名称

# ==================== 触发条件 ====================
on:
  # 推送触发
  push:
    branches: [main, master, develop]  # 推送到这些分支时触发

  # PR 触发
  pull_request:
    branches: [main, master]  # 向这些分支发起 PR 时触发

  # 定时触发（Cron 表达式）
  schedule:
    - cron: '0 18 * * *'  # UTC 18:00 = 北京时间凌晨 2:00
    # 格式: 分 时 日 月 周
    # '0 2 * * *'  = 每天 UTC 2:00
    # '0 */6 * * *' = 每 6 小时
    # '0 0 * * 1'  = 每周一 UTC 0:00

  # 手动触发（在 GitHub 页面点击按钮触发）
  workflow_dispatch:

# ==================== 环境变量 ====================
env:
  PYTHON_VERSION: '3.12'  # 全局环境变量，所有 job 可用

# ==================== 任务定义 ====================
jobs:
  test:  # job 名称
    runs-on: ubuntu-latest  # 运行环境（Linux/Windows/macOS）

    steps:
    # Step 1: 检出代码
    - name: Checkout code
      uses: actions/checkout@v4  # 使用官方 checkout action

    # Step 2: 配置 Python 环境
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ env.PYTHON_VERSION }}  # 引用环境变量
        cache: 'pip'  # 缓存 pip 依赖，加速后续构建

    # Step 3: 安装依赖
    - name: Install dependencies
      run: |  # 多行命令
        python -m pip install --upgrade pip
        pip install -r woniu_api_test/requirements.txt

    # Step 4: 运行测试
    - name: Run API tests
      working-directory: woniu_api_test  # 工作目录
      run: |
        pytest --alluredir=reports/allure-results -v --tb=short
      continue-on-error: true  # 即使测试失败也继续执行后续步骤

    # Step 5-7: 生成并部署 Allure 报告...
```

---

## 三、配置敏感信息（Secrets）

### 3.1 为什么需要 Secrets
- 测试账号密码不能明文写在配置文件中
- API Key、Token 等敏感信息需要安全存储
- Secrets 会被加密存储，日志中自动脱敏

### 3.2 添加 Secrets

**Step 1**: 进入仓库设置
```
GitHub 仓库页面 → Settings → Secrets and variables → Actions
```

**Step 2**: 点击 **New repository secret**

**Step 3**: 添加以下 Secrets
| Name | Value | 说明 |
|------|-------|-----|
| `TEST_PHONE` | 15983891506 | 测试账号手机号 |
| `TEST_PASSWORD` | xxxxxx | 测试账号密码 |
| `DINGTALK_TOKEN` | xxxxxx | 钉钉机器人 Token（可选） |

### 3.3 在配置中使用 Secrets

```yaml
- name: Run API tests
  working-directory: woniu_api_test
  env:
    TEST_PHONE: ${{ secrets.TEST_PHONE }}
    TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
  run: |
    pytest --alluredir=reports/allure-results -v
```

---

## 四、启用 GitHub Pages（报告托管）

### 4.1 配置步骤

**Step 1**: 进入仓库设置
```
GitHub 仓库页面 → Settings → Pages
```

**Step 2**: 配置 Source
- Source: **Deploy from a branch**
- Branch: **gh-pages** / **(root)**
- 点击 **Save**

**Step 3**: 首次运行后访问报告
```
https://你的用户名.github.io/仓库名/
```

### 4.2 注意事项
- 首次运行会自动创建 `gh-pages` 分支
- 报告部署需要几分钟生效
- 私有仓库的 Pages 仅付费用户可用，免费用户需改用公开仓库

---

## 五、查看运行结果

### 5.1 进入 Actions 页面
```
GitHub 仓库页面 → Actions
```

### 5.2 界面说明

```
┌─────────────────────────────────────────────────────────┐
│  All workflows                                          │
│  ├── API Tests ← 工作流名称                              │
│  │   ├── ✅ Initial commit (2m 35s)  ← 成功的运行       │
│  │   ├── ❌ Fix bug #123 (1m 20s)    ← 失败的运行       │
│  │   └── 🟡 Update tests (running)   ← 正在运行         │
└─────────────────────────────────────────────────────────┘
```

### 5.3 查看详细日志

点击某次运行 → 点击 job 名称（如 `test`）→ 展开各 step 查看日志

```
┌─────────────────────────────────────────────────────────┐
│  test                                                   │
│  ├── ✅ Set up job (2s)                                 │
│  ├── ✅ Checkout code (3s)                              │
│  ├── ✅ Set up Python (15s)                             │
│  ├── ✅ Install dependencies (45s)                      │
│  ├── ✅ Run API tests (2m 10s)  ← 点击查看测试日志       │
│  ├── ✅ Allure Report Action (30s)                      │
│  └── ✅ Deploy report to GitHub Pages (10s)             │
└─────────────────────────────────────────────────────────┘
```

---

## 六、手动触发运行

### 6.1 在 GitHub 页面触发

```
Actions → API Tests → Run workflow → 选择分支 → Run workflow
```

### 6.2 使用 GitHub CLI 触发

```bash
# 安装 GitHub CLI
brew install gh  # macOS
# 或 https://cli.github.com/ 下载

# 登录
gh auth login

# 触发工作流
gh workflow run api-test.yml --ref main
```

---

## 七、常见配置场景

### 7.1 只在特定文件变更时触发

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'woniu_api_test/**'  # 只有测试代码变更才触发
      - '.github/workflows/**'
```

### 7.2 并行运行多个环境

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
        environment: ['test', 'staging']

    steps:
    - name: Run tests on Python ${{ matrix.python-version }}
      run: pytest
```

### 7.3 测试失败发送钉钉通知

```yaml
notify:
  runs-on: ubuntu-latest
  needs: test
  if: failure()  # 只在测试失败时执行
  steps:
  - name: Send DingTalk notification
    run: |
      curl -X POST "${{ secrets.DINGTALK_WEBHOOK }}" \
        -H "Content-Type: application/json" \
        -d '{
          "msgtype": "markdown",
          "markdown": {
            "title": "API测试失败",
            "text": "## ❌ API 测试失败\n\n- 仓库: ${{ github.repository }}\n- 分支: ${{ github.ref }}\n- 提交: ${{ github.sha }}\n- [查看详情](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})"
          }
        }'
```

### 7.4 缓存依赖加速构建

```yaml
- name: Cache pip dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

---

## 八、调试技巧

### 8.1 查看环境变量
```yaml
- name: Debug - Print env
  run: env | sort
```

### 8.2 SSH 进入运行环境（调试用）
```yaml
- name: Setup tmate session
  uses: mxschmitt/action-tmate@v3
  if: ${{ failure() }}  # 只在失败时启用
  with:
    limit-access-to-actor: true
```

### 8.3 本地测试 Actions（使用 act）
```bash
# 安装 act
brew install act  # macOS

# 本地运行
act -j test
```

---

## 九、费用说明

### 9.1 免费额度（每月）

| 账户类型 | Linux | Windows | macOS |
|---------|-------|---------|-------|
| Free | 2000 分钟 | 无 | 无 |
| Pro | 3000 分钟 | 无 | 无 |
| Team | 3000 分钟 | 无 | 无 |

### 9.2 超出后收费
- Linux: $0.008/分钟
- Windows: $0.016/分钟
- macOS: $0.08/分钟

### 9.3 节省技巧
- 使用 `paths` 过滤触发
- 合理设置定时任务频率
- 使用缓存减少安装时间
- 私有仓库转公开可无限免费

---

## 十、Quick Start

1. **确保配置文件存在**
   ```
   .github/workflows/api-test.yml
   ```

2. **推送代码**
   ```bash
   git add .
   git commit -m "Add GitHub Actions CI"
   git push origin main
   ```

3. **查看运行**
   ```
   GitHub → Actions → 查看运行状态
   ```

4. **配置 Secrets**（如需要）
   ```
   Settings → Secrets → New repository secret
   ```

5. **启用 Pages**（报告托管）
   ```
   Settings → Pages → Source: gh-pages
   ```

---

## 附录：完整配置文件参考

见 `.github/workflows/api-test.yml`
