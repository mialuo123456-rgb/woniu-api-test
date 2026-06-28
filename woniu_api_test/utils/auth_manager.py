"""
登录态管理：登录获取 token，全局复用。
"""
import requests
from config.settings import TEST_ACCOUNT, validate_env
from utils.api_client import APIClient


class AuthManager:
    """管理登录 token，整个测试 session 只登录一次。"""

    _client = None
    _token = None

    @classmethod
    def login(cls, account=None):
        """登录并缓存 token，返回带 token 的 APIClient。"""
        if cls._client and cls._token:
            return cls._client

        # 验证环境变量
        if account is None:
            validate_env()
        account = account or TEST_ACCOUNT

        raw_client = APIClient()
        try:
            resp = raw_client.post("v2/Passport/login", json=account)
            resp.raise_for_status()
            data = resp.json()
        except requests.Timeout:
            raise RuntimeError("登录超时，请检查网络连接")
        except requests.RequestException as e:
            raise RuntimeError(f"登录请求失败: {e}")

        if data.get("error") != 0:
            raise RuntimeError(f"登录失败: {data}")

        cls._token = data["data"]["token"]["token"]
        user_id = data["data"]["token"].get("user_id", "")
        shop_id = data["data"].get("user", {}).get("shop_id") or account.get("shop_id", "")
        # 从 shops 列表中找到默认门店的 store_id
        stores = data["data"].get("user", {}).get("shops", [])
        store_id = ""
        for s in stores:
            if s.get("shop_id") == shop_id:
                store_id = s.get("store_id", "")
                break

        cls._client = APIClient(
            token=cls._token,
            shop=shop_id,
            store=store_id,
            snailuser=user_id,
        )
        return cls._client

    @classmethod
    def get_client(cls):
        """获取已登录的 APIClient（如未登录则自动登录）。"""
        if not cls._client:
            cls.login()
        return cls._client

    @classmethod
    def get_token(cls):
        if not cls._token:
            cls.login()
        return cls._token

    @classmethod
    def reset(cls):
        cls._client = None
        cls._token = None
