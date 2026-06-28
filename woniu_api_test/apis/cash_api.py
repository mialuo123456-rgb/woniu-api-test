"""
收银台相关 API
"""
from utils.api_client import APIClient


class CashAPI:
    """收银台类接口：购物车、下单、打印。"""

    def __init__(self, client: APIClient = None):
        self.client = client

    def get_cash_category(self, shop_id, member_id=-1):
        """GET v2/spu/cash_category — 收银台商品分类"""
        return self.client.get("v2/spu/cash_category", params={
            "shopping_card_id": 0, "member_id": member_id, "shop_id": shop_id
        })

    def get_cash_list(self, shop_id, keywords="", page=1, member_id=-1):
        """GET v2/spu/cash_list — 收银台商品列表"""
        return self.client.get("v2/spu/cash_list", params={
            "keywords": keywords, "page": page, "member_id": member_id,
            "spu_category_id": -2, "category_type": -2, "shop_id": shop_id
        })

    def add_to_cart(self, shop_id, product_id, num=1, **extra):
        """POST v2/carts/add_product — 添加商品到购物车"""
        payload = {
            "shop_id": shop_id, "activity_id": None, "activity_auto_id": None,
            "product_id": product_id, "cart_type": 0, "out_id": 0,
            "num": num, "version": 1, "notice_vip": 1,
        }
        payload.update(extra)
        return self.client.post("v2/carts/add_product", json=payload)

    def change_member(self, shop_id, member_id=-1, cart_type=0, out_id=0):
        """POST v2/cats/change_member — 切换会员"""
        return self.client.post("v2/cats/change_member", json={
            "shop_id": shop_id, "member_id": member_id,
            "cart_type": cart_type, "out_id": out_id
        })

    def get_cart_list(self, shop_id, is_reset_price=1):
        """GET v2/carts/list — 购物车列表"""
        return self.client.get("v2/carts/list", params={
            "shop_id": shop_id, "cart_type": 0, "out_id": 0,
            "is_reset_price": is_reset_price
        })

    def get_cart_count(self, shop_id):
        """GET v2/cart/count — 购物车数量"""
        return self.client.get("v2/cart/count", params={"shopId": shop_id, "shop_id": shop_id})

    def build_order(self, shop_id, pay_ways, price, **extra):
        """POST v2/carts/build_order_new — 创建订单"""
        payload = {
            "shop_id": shop_id, "cart_type": 0, "out_id": 0,
            "pay_ways": pay_ways, "order_time": 0, "mark": "",
            "is_spending_msg": 0, "price": price,
        }
        payload.update(extra)
        return self.client.post("v2/carts/build_order_new", json=payload)

    def get_pay_way_list(self, shop_id, scene=1):
        """GET v2/shop_pay_way/list — 支付方式列表"""
        return self.client.get("v2/shop_pay_way/list", params={"scene": scene, "shop_id": shop_id})

    def get_print_data(self, shop_id, order_id, kind=1):
        """GET v2/print/data — 打印小票数据"""
        return self.client.get("v2/print/data", params={
            "order_id": order_id, "kind": kind, "out_id": 0, "shop_id": shop_id
        })

    def get_species_list(self, shop_id):
        """GET v2/Species/getLevel — 宠物种类"""
        return self.client.get("v2/Species/getLevel", params={"shop_id": shop_id})

    def get_wechat_qr(self, shop_id, qr_type=0):
        """GET v2/mall/we_chat_qr_image — 微信二维码"""
        return self.client.get("v2/mall/we_chat_qr_image", params={
            "shop_id": shop_id, "type": qr_type, "version": 1
        })

    def clear_cart(self, shop_id, max_attempts=5):
        """清空购物车：处理正常商品和已删除商品

        :param shop_id: 门店 ID
        :param max_attempts: 最大尝试次数（防止无限循环）
        """
        import re

        for _ in range(max_attempts):
            resp = self.get_cart_list(shop_id)
            data = resp.json()

            # 情况1：购物车有已删除的商品，从错误消息中提取 product_id
            if data.get("error") != 0:
                message = data.get("message", "")
                # 匹配 "请清空购物车再试104534675" 中的数字
                match = re.search(r"再试(\d+)", message)
                if match:
                    deleted_product_id = int(match.group(1))
                    self.add_to_cart(shop_id, deleted_product_id, num=-1)
                    continue
                # 其他错误直接返回
                break

            # 情况2：正常获取到购物车列表，逐个减掉商品
            products = data.get("data", {}).get("products") or []
            if not products:
                break  # 购物车已空

            for product in products:
                product_id = product.get("product_id")
                num = product.get("num", 0)
                if product_id and num > 0:
                    self.add_to_cart(shop_id, product_id, num=-num)

        # 切换非会员来重置购物车状态
        return self.change_member(shop_id, member_id=-1)
