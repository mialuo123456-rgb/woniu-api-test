# 蜗牛小店接口自动化测试计划

> 生成时间：2026-06-27
> 项目路径：woniu_api_test

---

## 一、项目现状

### 1.1 已有工具栈

| 工具 | 用途 | 状态 |
|-----|------|------|
| pytest | 测试框架 | ✅ 已集成 |
| requests | HTTP 客户端 | ✅ 已集成 |
| allure | 测试报告 | ✅ 已集成 |
| YAML | 数据驱动 | ✅ 已集成 |
| 关键字驱动 | 复用封装 | ✅ 已集成 |

### 1.2 当前项目结构

```
woniu_api_test/
├── apis/           # API 封装层
├── testcases/      # 测试用例
├── testdata/       # 测试数据（YAML）
├── keywords/       # 关键字库
├── utils/          # 工具类
├── config/         # 配置文件
├── reports/        # Allure 报告
└── conftest.py     # pytest 全局配置
```

### 1.3 测试覆盖现状

| 模块 | 接口数 | 已覆盖 | 覆盖率 | 用例数 |
|-----|--------|--------|--------|--------|
| 商品管理 | 24 | 17 | 70.8% | 38 |
| 会员管理 | - | - | - | - |
| 收银台 | - | - | - | 31 |
| 认证登录 | - | - | - | 14 |

---

## 二、工具补充建议

### 2.1 接口录制与生成

| 工具 | 作用 | 优先级 |
|-----|------|--------|
| **mitmproxy** | 代理录制接口请求 | 中 |
| **Playwright** | 浏览器操作 + 网络监听，实现"点击页面自动录制API" | 高 |

### 2.2 接口文档同步

| 工具 | 作用 | 优先级 |
|-----|------|--------|
| **Swagger/OpenAPI** | 接口文档 → 自动生成用例骨架 | 中 |
| **Apifox/Postman** | 团队协作 + 用例管理 | 低 |

### 2.3 Mock 与环境隔离

| 工具 | 作用 | 优先级 |
|-----|------|--------|
| **responses** | Mock HTTP 响应，隔离外部依赖 | 中 |
| **pytest-docker** | 启动测试环境容器 | 低 |

### 2.4 CI/CD 集成

| 工具 | 作用 | 优先级 |
|-----|------|--------|
| **GitHub Actions** | 自动化运行测试 | 高 |
| **GitLab CI** | 自动化运行测试（备选） | 中 |
| **Jenkins** | 定时执行 + 报告推送 | 低 |

---

## 三、架构优化建议

### 3.1 建议新增目录

```
woniu_api_test/
├── ...（现有目录）
├── fixtures/           # 共享 fixture（数据准备/清理）
├── schemas/            # JSON Schema（响应结构校验）
├── generators/         # 测试数据生成器（Faker）
└── scripts/            # 辅助脚本
    ├── record_api.py       # API 录制脚本
    └── generate_case.py    # 用例生成脚本
```

### 3.2 代码规范建议

- **API 层**：每个模块一个文件，方法命名统一（get_xxx, create_xxx, delete_xxx）
- **测试层**：按 Unit / Integration / Scenario 分层，使用 pytest.mark 标记
- **数据层**：YAML 文件按模块拆分，支持环境切换
- **断言封装**：统一的响应校验方法，支持 JSON Schema 验证

---

## 四、实施计划

### 第一阶段：完善基础（1-2周）

| 任务 | 优先级 | 状态 |
|-----|--------|------|
| 补齐商品模块高优先级测试用例（compute_in_price, get_file_sts） | P0 | 待开始 |
| 增加 JSON Schema 校验响应结构 | P1 | 待开始 |
| 统一异常处理和断言封装 | P1 | 待开始 |
| 完善 conftest.py 公共 fixture | P1 | 部分完成 |

### 第二阶段：提升效率（2-4周）

| 任务 | 优先级 | 状态 |
|-----|--------|------|
| 集成 Playwright 实现"页面操作 → 录制 API → 生成用例" | P0 | 待开始 |
| 增加测试数据生成器（Faker） | P1 | 待开始 |
| CI/CD 集成（GitHub Actions） | P1 | 待开始 |
| 接口覆盖率统计 | P2 | 待开始 |

### 第三阶段：持续优化（长期）

| 任务 | 优先级 | 状态 |
|-----|--------|------|
| 性能测试集成（locust） | P2 | 待开始 |
| 契约测试（如果有微服务） | P3 | 待开始 |
| 测试报告推送（钉钉/企微） | P2 | 待开始 |
| 多环境支持（test/staging/prod） | P1 | 待开始 |

---

## 五、商品模块待补充用例

### 5.1 高优先级（必须补充）

#### compute_in_price 计算入库价格

```python
@pytest.mark.unit
class TestComputeInPrice:
    """计算入库价格 - 独立单元测试"""

    def test_compute_in_price_normal(self):
        """正常：标准入库价格计算"""

    def test_compute_in_price_zero_number(self):
        """边界：入库数量为0"""

    def test_compute_in_price_large_number(self):
        """边界：超大数量"""

    def test_compute_in_price_negative(self):
        """异常：负数价格"""

    def test_compute_in_price_invalid_product(self):
        """异常：不存在的商品ID"""
```

#### get_file_sts 文件上传凭证

```python
@pytest.mark.unit
class TestFileSTS:
    """文件上传凭证 - 单元测试"""

    def test_get_file_sts_success(self):
        """正常：获取有效凭证"""

    def test_get_file_sts_credentials_structure(self):
        """验证：凭证结构完整性"""

    def test_get_file_sts_invalid_token(self):
        """异常：无效token"""

    def test_get_file_sts_missing_params(self):
        """异常：缺少必要参数"""
```

### 5.2 中优先级（建议补充）

| 接口 | 缺失场景 |
|-----|---------|
| get_sku_list | list_kind 参数全覆盖 |
| get_category_list | 分类层级结构验证 |
| get_brand_by_name | 空结果处理 |
| save_spu (编辑) | 编辑现有 SPU |

---

## 六、CI/CD 配置示例

### GitHub Actions 配置

```yaml
# .github/workflows/api-test.yml
name: API Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点执行

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run tests
      run: |
        cd woniu_api_test
        pytest --alluredir=reports/allure-results

    - name: Generate Allure Report
      uses: simple-elf/allure-report-action@master
      if: always()
      with:
        allure_results: woniu_api_test/reports/allure-results
        allure_history: allure-history

    - name: Deploy report to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      if: always()
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: allure-history
```

---

## 七、参考资源

- [pytest 官方文档](https://docs.pytest.org/)
- [Allure Report](https://docs.qameta.io/allure/)
- [Playwright Python](https://playwright.dev/python/)
- [JSON Schema](https://json-schema.org/)
- [Faker](https://faker.readthedocs.io/)

---

## 八、更新记录

| 日期 | 内容 | 作者 |
|-----|------|------|
| 2026-06-27 | 初始版本，完成现状分析和计划制定 | Claude |
