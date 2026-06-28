"""
单元接口测试 —— 认证模块（增强版）
覆盖维度：正常 / 边界 / 异常 / 安全
"""
import pytest
from apis.auth_api import AuthAPI
from utils.api_client import APIClient
from utils.data_loader import load_yaml

config = load_yaml("config.yaml")


def _login(payload):
    """快捷登录请求（不走 token 缓存，需携带版本头）。"""
    client = APIClient()
    return client.post("v2/Passport/login", json=payload)


class TestAuthLogin:
    """登录接口：正常 / 异常 / 边界 / 安全"""

    @pytest.fixture(scope="class")
    def auth_api(self, api_client):
        return AuthAPI(api_client)

    # ===== 正常用例 =====

    def test_login_success(self):
        """正常登录：返回 200 且包含有效 token"""
        resp = _login(config["test_account"]["valid"])
        data = resp.json()
        assert resp.status_code == 200
        assert data["error"] == 0
        token_info = data["data"]["token"]
        assert isinstance(token_info["token"], str)
        assert len(token_info["token"]) > 0
        assert isinstance(token_info["user_id"], int)
        assert token_info["ttl"] > 0
        # 验证 user 信息
        user = data["data"]["user"]
        assert user["phone"] == config["test_account"]["valid"]["phone"]
        assert isinstance(user["shops"], list)
        assert len(user["shops"]) > 0

    # ===== 异常用例 =====

    def test_login_wrong_password(self):
        """异常：错误密码"""
        resp = _login(config["test_account"]["invalid_password"])
        data = resp.json()
        assert resp.status_code == 200
        assert data["error"] != 0
        assert "data" not in data or data.get("data") is None

    def test_login_invalid_phone(self):
        """异常：不存在的手机号"""
        resp = _login(config["test_account"]["invalid_phone"])
        data = resp.json()
        assert data["error"] != 0

    def test_login_empty_phone(self):
        """异常：手机号为空"""
        resp = _login(config["test_account"]["empty_phone"])
        data = resp.json()
        assert data["error"] != 0

    def test_login_empty_password(self):
        """异常：密码为空"""
        resp = _login(config["test_account"]["empty_password"])
        data = resp.json()
        assert data["error"] != 0

    # ===== 安全用例 =====

    def test_login_sql_injection(self):
        """安全：SQL 注入密码"""
        resp = _login(config["test_account"]["sql_injection"])
        data = resp.json()
        assert data["error"] != 0
        # 确保没有返回有效 token
        assert not data.get("data") or "token" not in (data.get("data") or {})

    def test_login_xss_injection(self):
        """安全：XSS 脚本手机号"""
        resp = _login(config["test_account"]["xss_injection"])
        data = resp.json()
        assert data["error"] != 0

    def test_login_missing_fields(self):
        """异常：请求体缺少必填字段"""
        resp = _login({"phone": "15983891506"})
        data = resp.json()
        assert data["error"] != 0


class TestUserInfo:
    """用户信息接口：正常 / 边界 / 异常"""

    @pytest.fixture(scope="class")
    def auth_api(self, api_client):
        return AuthAPI(api_client)

    def test_get_user_info_success(self, auth_api, shop_id):
        """正常：获取用户信息"""
        resp = auth_api.get_user_info(shop_id)
        data = resp.json()
        assert data["error"] == 0
        user = data["data"]
        assert isinstance(user["user_id"], int)
        assert isinstance(user["phone"], str)
        assert len(user["phone"]) == 11
        assert isinstance(user["shops"], list)
        assert len(user["shops"]) > 0

    def test_get_user_info_invalid_shop(self, auth_api):
        """边界：无效 shop_id"""
        resp = auth_api.get_user_info(config["shop"]["invalid_shop_id"])
        data = resp.json()
        # 接口应能处理无效 shop（不崩溃）
        assert resp.status_code == 200

    def test_get_shop_certification(self, auth_api, shop_id):
        """正常：门店认证信息"""
        resp = auth_api.get_shop_certification(shop_id)
        data = resp.json()
        assert data["error"] == 0
        cert = data["data"]
        assert isinstance(cert["name"], str)
        assert len(cert["name"]) > 0
        assert "shop_type_name" in cert

    def test_get_plus_info(self, auth_api, shop_id):
        """正常：Plus 版本信息"""
        resp = auth_api.get_plus_info(shop_id)
        data = resp.json()
        assert data["error"] == 0
        plus = data["data"]
        assert "vip_plus" in plus
        assert "chain_plus" in plus

    def test_get_staff_list(self, auth_api, shop_id):
        """正常：门店员工列表"""
        resp = auth_api.get_staff(shop_id)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], list)
        if len(data["data"]) > 0:
            staff = data["data"][0]
            assert "user_id" in staff
            assert "user_name" in staff

    def test_get_message_setting(self, auth_api, shop_id):
        """正常：消息设置"""
        resp = auth_api.get_message_setting(shop_id)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], dict)
        assert "setting" in data["data"]
