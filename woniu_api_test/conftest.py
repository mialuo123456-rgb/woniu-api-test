"""
pytest 全局配置：登录态注入 + Allure 报告增强
"""
import os
import json
import time
import logging
import pytest
import allure

from utils.auth_manager import AuthManager
from config.settings import BASE_URL, DEFAULT_SHOP_ID, TEST_ACCOUNT, RATE_LIMIT_DELAY
from apis.cash_api import CashAPI


# ===== 日志配置 =====

def pytest_configure(config):
    """配置测试日志格式。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


# ===== 全局限流保护 =====

@pytest.fixture(autouse=True)
def slow_down():
    """每个用例执行前等待，避免服务器频率限制（LT001）。"""
    time.sleep(RATE_LIMIT_DELAY)


# ===== Session 级 Fixtures =====

@pytest.fixture(scope="session")
def api_client():
    """整个测试会话只登录一次，所有用例共享同一个带 token 的 client。"""
    return AuthManager.get_client()


@pytest.fixture(scope="session")
def shop_id():
    return DEFAULT_SHOP_ID


@pytest.fixture(scope="function")
def clean_cart(api_client, shop_id):
    """函数级 fixture：每个测试前清空购物车，确保测试环境干净"""
    cash_api = CashAPI(api_client)
    cash_api.clear_cart(shop_id)
    yield
    # 测试结束后再次清空（清理本次测试产生的数据）
    cash_api.clear_cart(shop_id)


# ===== Allure 环境信息 =====

def pytest_sessionstart(session):
    """测试会话开始时写入 allure 环境信息。"""
    allure_dir = os.path.join(os.path.dirname(__file__), "reports", "allure-results")
    os.makedirs(allure_dir, exist_ok=True)
    env_props = {
        "Environment": "测试环境 (test)",
        "Base_URL": BASE_URL,
        "Test_Account": TEST_ACCOUNT["phone"],
        "Shop_ID": str(DEFAULT_SHOP_ID),
        "Framework": "pytest + requests + allure",
        "Python": os.popen("python --version 2>&1").read().strip(),
    }
    env_path = os.path.join(allure_dir, "environment.properties")
    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in env_props.items():
            f.write(f"{k}={v}\n")


# ===== 自动给用例添加 Allure 分层标记 =====

def pytest_collection_modifyitems(items):
    """根据测试文件路径自动添加 allure 分层标签。"""
    for item in items:
        path = str(item.fspath)
        if "/unit/" in path or "\\unit\\" in path:
            item.add_marker(allure.epic("蜗牛小店接口测试"))
            item.add_marker(allure.feature("单元接口测试"))
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in path or "\\integration\\" in path:
            item.add_marker(allure.epic("蜗牛小店接口测试"))
            item.add_marker(allure.feature("集成接口测试"))
            item.add_marker(pytest.mark.integration)
        elif "/scenario/" in path or "\\scenario\\" in path:
            item.add_marker(allure.epic("蜗牛小店接口测试"))
            item.add_marker(allure.feature("业务场景测试"))
            item.add_marker(pytest.mark.scenario)


# ===== Allure 附件工具 =====

def allure_attach_response(resp, title="接口响应"):
    """将接口响应附加到 allure 报告。"""
    allure.attach(
        json.dumps(resp.json(), ensure_ascii=False, indent=2),
        name=title,
        attachment_type=allure.attachment_type.JSON,
    )


def allure_attach_request(method, url, payload=None, title="接口请求"):
    """将接口请求附加到 allure 报告。"""
    content = f"Method: {method}\nURL: {url}"
    if payload:
        content += f"\nBody:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    allure.attach(content, name=title, attachment_type=allure.attachment_type.TEXT)
