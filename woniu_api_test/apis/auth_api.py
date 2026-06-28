"""
认证相关 API
"""
from utils.api_client import APIClient
from config.settings import TEST_ACCOUNT


class AuthAPI:
    """登录、用户信息相关接口。"""

    def __init__(self, client: APIClient = None):
        self.client = client

    def login(self, phone=None, password=None, shop_id=None):
        """POST v2/Passport/login — 用户登录"""
        payload = {
            "phone": phone or TEST_ACCOUNT["phone"],
            "password": password or TEST_ACCOUNT["password"],
            "shop_id": shop_id or TEST_ACCOUNT["shop_id"],
        }
        return self.client.post("v2/Passport/login", json=payload)

    def get_user_info(self, shop_id):
        """GET v2/User/getUserInfo — 获取用户信息"""
        return self.client.get("v2/User/getUserInfo", params={"shop_id": shop_id})

    def get_shop_certification(self, shop_id):
        """GET v2/Shop/Certification/get — 门店认证信息"""
        return self.client.get("v2/Shop/Certification/get", params={"shopId": shop_id, "shop_id": shop_id})

    def get_plus_info(self, shop_id):
        """GET v2/activation/plus/info — Plus 版本信息"""
        return self.client.get("v2/activation/plus/info", params={"shopId": shop_id, "shop_id": shop_id})

    def get_message_setting(self, shop_id):
        """GET v2/Shop/getMessageSetting — 消息设置"""
        return self.client.get("v2/Shop/getMessageSetting", params={"shopId": shop_id, "shop_id": shop_id})

    def get_staff(self, shop_id):
        """GET v2/Shop/getStaff — 门店员工列表"""
        return self.client.get("v2/Shop/getStaff", params={
            "shopId": shop_id, "is_all": 1, "user_store_power": 1, "shop_id": shop_id
        })
