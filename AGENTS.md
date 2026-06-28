# AGENTS.md — 蜗牛小店接口自动化测试项目

> 本文件为 AI 编程助手（Claude Code / Qoder AI 等）提供项目上下文和编码规范。

## 项目简介

蜗牛小店（蜗牛小点）Web 端接口自动化测试框架。基于 **pytest + requests + allure**，采用分层架构，覆盖登录、商品管理、收银台、会员等核心业务模块。

- **测试环境：** https://webtest.woniuxiaodian.cn
- **测试账号：** 15983891506 / luoting520，门店 shop_id=6419，store_id=5238
- **接口录制文档：** 项目根目录下 `api-recording-*.md` 文件

## 技术栈

| 类别 | 技术 |
|------|------|
| 测试框架 | pytest 7.x |
| HTTP 库 | requests（基于 Session 复用） |
| 数据格式 | YAML（测试数据驱动） |
| 报告 | allure-pytest |
| Python | 3.x |

## 目录结构

```
woniu_api_test/
├── apis/                    # API 定义层（每个业务模块一个类）
│   ├── auth_api.py          # 认证接口（登录）
│   ├── cash_api.py          # 收银台接口
│   ├── member_api.py        # 会员接口
│   └── product_api.py       # 商品管理接口
├── config/
│   └── settings.py          # 全局配置（URL、账号、超时等）
├── testcases/               # 测试用例（分层）
│   ├── unit/                # 单元接口测试
│   ├── integration/         # 集成接口测试
│   └── scenario/            # 业务场景测试
│   ├── test_cash.py         # 收银台全量用例
│   └── test_product.py      # 商品管理全量用例
├── testdata/                # YAML 测试数据
│   ├── config.yaml
│   ├── cash_data.yaml
│   └── product_data.yaml
├── utils/                   # 工具层
│   ├── api_client.py        # HTTP 客户端封装（含签名）
│   ├── auth_manager.py      # 登录态管理
│   └── data_loader.py       # YAML 数据加载器
├── conftest.py              # pytest 全局配置 + fixtures
├── pytest.ini               # pytest 配置
├── requirements.txt
└── run_tests.py             # 运行入口
```

## 架构说明

### 分层架构

```
apis/  (API 定义层 — 封装接口请求)
  ↓ 依赖
utils/ (工具层 — HTTP客户端/认证/数据加载)
  ↓ 依赖
config/ (配置层 — 环境地址/账号/超时)
```

测试用例调用 `apis/` 层发起请求，`apis/` 层调用 `utils/APIClient` 发送 HTTP。

### 核心机制

1. **APIClient（`utils/api_client.py`）**
   - 基于 `requests.Session`，自动携带 token
   - **签名计算：** `MD5(shop|store|uri|token|Request-Time)` — 每次请求动态生成
   - 请求头携带：`token`、`shop`、`store`、`snailuser`、`Signature`、`Request-Time`、`Client-Version`

2. **AuthManager（`utils/auth_manager.py`）**
   - Session 级别单例，整个测试会话只登录一次
   - 登录后自动提取 token、shop_id、store_id

3. **conftest.py**
   - `api_client` fixture：Session 级共享已登录客户端
   - `slow_down` autouse fixture：每个用例间隔 0.3 秒（防限流）
   - 自动按目录路径添加 allure 分层标签

## 编码规范

### 新增接口定义

在 `apis/` 对应模块文件中添加方法，遵循以下格式：

```python
def get_xxx(self, shop_id, **kwargs):
    """GET v2/xxx — 一句话描述"""
    return self.client.get("v2/xxx", params={"shop_id": shop_id, ...})
```

### 新增测试用例

- **单元测试** → `testcases/unit/test_xxx_api.py`
- **集成测试** → `testcases/integration/`
- **场景测试** → `testcases/scenario/`

```python
class TestXxx:
    """接口名：正常 / 异常 / 边界 / 安全"""

    @pytest.mark.unit
    def test_xxx_normal(self, api_client, shop_id):
        xxx_api = XxxAPI(api_client)
        resp = xxx_api.do_something(shop_id)
        assert resp.json()["error"] == 0
```

### 断言约定

统一使用响应体的 `error` 字段判断成功失败：
```python
assert resp.json()["error"] == 0   # 成功
assert resp.json()["success"] is True
```

### 测试数据

用 YAML 管理在 `testdata/` 目录，通过 `load_yaml()` 加载：

```python
from utils.data_loader import load_yaml
data = load_yaml("product_data.yaml")
```

## 运行测试

```bash
cd woniu_api_test
pip install -r requirements.txt

# 全部测试
python run_tests.py

# 按层级运行
python run_tests.py --level unit
python run_tests.py --level integration
python run_tests.py --level scenario

# 不生成报告
python run_tests.py --no-report

# 直接用 pytest
python -m pytest testcases/ -v
python -m pytest testcases/unit/ -v -m unit

# 查看 allure 报告
python run_tests.py --serve
```

## 注意事项

1. **签名是必须的** — 所有需认证的接口都要经过 APIClient 发送（它会自动签名），不要绕过直接用 requests
2. **测试限流** — conftest.py 中有 0.3 秒间隔保护，避免请求过快
3. **数据隔离** — 创建型测试用例必须自行清理数据（删除创建的商品/会员等）
4. **token 生命周期** — token 有效期 30 天（ttl=2592000），测试中 Session 级别复用即可
5. **接口路径前缀** — 调用时用相对路径如 `v2/sku/add`，APIClient 会自动拼接 BASE_URL

## 接口录制 Skill

项目配合三个自定义 skill 使用（位于 `~/.qoder-cn/skills/`）：

1. **api-recorder** — 录制网页操作触发 API 调用，生成 markdown 接口文档
2. **api-doc-to-testcases** — 将接口文档自动转换为 pytest 测试用例
3. **midscene-automation** — AI 视觉驱动 UI 自动化，配合接口录制
