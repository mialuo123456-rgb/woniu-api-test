"""
会员相关 API
"""
from utils.api_client import APIClient


class MemberAPI:
    """会员类接口。"""

    def __init__(self, client: APIClient = None):
        self.client = client

    # ========== 会员基础接口 ==========

    def get_member_list(self, shop_id, keywords="", order_by="updated", page=1,
                        rfm_level=0, is_order_asc=0):
        """GET v2/Members/get_list/new_simple — 会员列表"""
        return self.client.get("v2/Members/get_list/new_simple", params={
            "orderBy": order_by, "shopId": shop_id, "shop_id": shop_id,
            "keywords": keywords, "page": page, "rfm_level": rfm_level,
            "is_order_asc": is_order_asc, "is_mini_login": 0
        })

    def get_member_by_id(self, shop_id, member_id):
        """GET v2/Members/getById — 会员详情"""
        return self.client.get("v2/Members/getById", params={
            "memberId": member_id, "shopId": shop_id, "shop_id": shop_id
        })

    def add_member(self, member_data):
        """POST v2/Members/add — 新增会员"""
        return self.client.post("v2/Members/add", json=member_data)

    def get_member_once_cards(self, shop_id, member_id_or_store_id, member_id=None):
        """GET v2/Members/getMemberOnceCards — 会员次卡

        兼容两种调用方式:
        - get_member_once_cards(shop_id, member_id)
        - get_member_once_cards(shop_id, store_id, member_id)
        """
        if member_id is None:
            # 新调用方式: (shop_id, member_id)
            actual_member_id = member_id_or_store_id
        else:
            # 旧调用方式: (shop_id, store_id, member_id)
            actual_member_id = member_id
        return self.client.get("v2/Members/getMemberOnceCards", params={
            "shopId": shop_id, "shop_id": shop_id, "memberId": actual_member_id
        })

    def get_member_shopping_cards(self, shop_id, member_id, page=1, limit=99, status=1):
        """GET v2/shopping_card/get/list/for/member — 会员购物卡"""
        return self.client.get("v2/shopping_card/get/list/for/member", params={
            "shopId": shop_id, "shop_id": shop_id, "member_id": member_id,
            "page": page, "limit": limit, "status": status
        })

    def get_balance_log(self, shop_id, store_id, member_id, actions=None, page=1, limit=10):
        """GET v2/member/balance/log — 会员余额日志"""
        params = {
            "shop_id": shop_id, "store_id": store_id, "member_id": member_id,
            "page": page, "limit": limit
        }
        if actions:
            params["actions[]"] = actions
        return self.client.get("v2/member/balance/log", params=params)

    # ========== 会员标签接口 ==========

    def get_default_tags(self, shop_id, store_id):
        """GET v2/member/tags/default_list — 默认标签列表"""
        return self.client.get("v2/member/tags/default_list", params={
            "shop_id": shop_id, "store_id": store_id
        })

    def add_shop_tag(self, shop_id, store_id, name):
        """POST v2/shop/tags/add — 新增店铺标签"""
        return self.client.post("v2/shop/tags/add", json={
            "name": name, "shop_id": shop_id, "store_id": store_id
        })

    # ========== RFM 等级接口 ==========

    def get_rfm_level_list(self, shop_id):
        """GET v2/member/rfm_level_list — RFM 等级列表"""
        return self.client.get("v2/member/rfm_level_list", params={
            "shop_id": shop_id
        })

    # ========== 宠物品种接口 ==========

    def get_species_level(self, shop_id):
        """GET v2/Species/getLevel — 宠物品种列表"""
        return self.client.get("v2/Species/getLevel", params={
            "shop_id": shop_id
        })

    # ========== 店铺相关接口 ==========

    def get_staff_list(self, shop_id, is_all=1, user_store_power=2):
        """GET v2/Shop/getStaff — 员工列表"""
        return self.client.get("v2/Shop/getStaff", params={
            "shopId": shop_id, "shop_id": shop_id,
            "is_all": is_all, "user_store_power": user_store_power
        })

    def get_shop_once_cards(self, shop_id):
        """GET v2/Shop/getOnceCards — 店铺次卡列表"""
        return self.client.get("v2/Shop/getOnceCards", params={
            "shopId": shop_id, "shop_id": shop_id
        })

    def get_member_level_list(self, shop_id):
        """GET v2/Shop/getMemberLevelList — 会员等级列表"""
        return self.client.get("v2/Shop/getMemberLevelList", params={
            "shopId": shop_id, "shop_id": shop_id
        })

    def get_shopping_card_list(self, shop_id, page=1, limit=99):
        """GET v2/shopping_card/get/list — 购物卡列表"""
        return self.client.get("v2/shopping_card/get/list", params={
            "shopId": shop_id, "shop_id": shop_id, "page": page, "limit": limit
        })

    # ========== 营销活动接口 ==========

    def get_marketing_activity_list(self, shop_id, status=100, level_ids=-1, kinds=1):
        """GET v2/marketing_activity/list — 营销活动列表"""
        return self.client.get("v2/marketing_activity/list", params={
            "shop_id": shop_id, "status": status, "level_ids": level_ids, "kinds": kinds
        })

    # ========== 用户设置接口 ==========

    def get_user_store_setting(self, shop_id, key):
        """GET v2/user_store_setting/value — 用户门店设置"""
        return self.client.get("v2/user_store_setting/value", params={
            "shop_id": shop_id, "key": key
        })
