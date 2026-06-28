"""
商品管理相关 API
"""
import time
import logging
from utils.api_client import APIClient
from config.settings import RETRY_MAX_ATTEMPTS, RETRY_BASE_DELAY, RETRY_BACKOFF

logger = logging.getLogger(__name__)


class ProductAPI:
    """商品管理类接口。"""

    def __init__(self, client: APIClient = None):
        self.client = client

    def get_spu_list(self, shop_id, page=1, limit=15, keywords="", **extra):
        """GET v2/spu/manage_list — 商品列表"""
        params = {
            "page": page, "limit": limit, "statistics": 1, "keywords": keywords,
            "spu_category_id": 0, "tags": "", "tag_is_in": 1, "order_by": 2,
            "is_order_asc": 0, "with_sku": 1, "is_sum": 1, "is_off": 0,
            "spu_list_kind": 0, "shop_id": shop_id,
        }
        params.update(extra)
        return self.client.get("v2/spu/manage_list", params=params)

    def get_sku_list(self, shop_id, page=1, limit=30, list_kind=1):
        """GET v2/sku/list — SKU 列表"""
        return self.client.get("v2/sku/list", params={
            "page": page, "limit": limit, "list_kind": list_kind, "shop_id": shop_id
        })

    def get_by_barcode(self, bar_code, shop_id):
        """GET v2/Product/getByBarCode — 条码查商品"""
        return self.client.get("v2/Product/getByBarCode", params={
            "barCode": bar_code, "shop_id": shop_id
        })

    def add_sku(self, sku_data, retry=True):
        """POST v2/sku/add — 新建商品

        :param sku_data: 商品数据
        :param retry: 是否启用频率限制重试（默认 True）
        """
        if not retry:
            return self.client.post("v2/sku/add", json=sku_data)

        # 带重试的创建逻辑
        for attempt in range(RETRY_MAX_ATTEMPTS):
            resp = self.client.post("v2/sku/add", json=sku_data)
            data = resp.json()

            # 检查是否为频率限制错误
            if data.get("error") != 0:
                msg = data.get("message", "")
                # 常见频率限制关键词：频繁、too many、rate limit、请稍后
                if any(kw in msg for kw in ["频繁", "稍后", "too many", "rate", "limit"]):
                    if attempt < RETRY_MAX_ATTEMPTS - 1:
                        wait_time = RETRY_BASE_DELAY * (RETRY_BACKOFF ** attempt)
                        logger.warning(f"[重试] 创建商品频率限制，等待 {wait_time:.1f}s 后重试 ({attempt + 1}/{RETRY_MAX_ATTEMPTS})")
                        time.sleep(wait_time)
                        continue

            return resp

        return resp

    def delete_by_ids(self, shop_id, product_ids):
        """POST v2/Product/delByIds — 删除商品"""
        return self.client.post("v2/Product/delByIds", data={
            "shopId": shop_id, "product_ids": product_ids, "shop_id": shop_id
        })

    def update_stocks(self, shop_id, product_id, number, mark="操作入库"):
        """POST v2/product/update/stocks — 商品入库"""
        return self.client.post("v2/product/update/stocks", json={
            "shopId": shop_id, "productId": product_id, "number": number,
            "mark": mark, "shop_id": shop_id
        })

    def get_category_list(self, shop_id):
        """GET v2/merchant/category/list — 商品分类列表"""
        return self.client.get("v2/merchant/category/list", params={"shop_id": shop_id})

    def get_shop_categories(self, shop_id):
        """GET v2/Shop/getCategories — 门店分类"""
        return self.client.get("v2/Shop/getCategories", params={"shopId": shop_id, "shop_id": shop_id})

    def get_product_tags(self, shop_id):
        """GET v2/product_tags/list — 商品标签列表"""
        return self.client.get("v2/product_tags/list", params={"shop_id": shop_id})

    def save_product_tag(self, shop_id, name):
        """POST v2/product_tags/save — 新建标签"""
        return self.client.post("v2/product_tags/save", json={"shop_id": shop_id, "name": name})

    def get_brand_list(self, shop_id):
        """GET v2/merchant/brand/list — 品牌列表"""
        return self.client.get("v2/merchant/brand/list", params={"shop_id": shop_id})

    def get_brand_by_name(self, product_name, shop_id):
        """GET v2/merchant/brand/get/by_product_name — 根据商品名查品牌"""
        return self.client.get("v2/merchant/brand/get/by_product_name", params={
            "product_name": product_name, "shop_id": shop_id
        })

    def get_supplier_list(self, shop_id):
        """GET v2/shop/supplier/list — 供应商列表"""
        return self.client.get("v2/shop/supplier/list", params={"shop_id": shop_id})

    def save_supplier(self, supplier_data):
        """POST v2/shop/supplier/save — 新建/编辑供应商"""
        return self.client.post("v2/shop/supplier/save", json=supplier_data)

    def delete_supplier(self, shop_id, supplier_id):
        """POST v2/shop/supplier/delete — 删除供应商"""
        return self.client.post("v2/shop/supplier/delete", json={
            "shop_id": shop_id,
            "id": supplier_id
        })

    def get_file_sts(self, shop_id, token):
        """GET v2/file/sts — 文件上传凭证"""
        return self.client.get("v2/file/sts", params={"token": token, "shop_id": shop_id})

    # === 批量入库 ===

    def compute_in_price(self, shop_id, product_id, in_number, in_price):
        """GET v2/product/compute/in_price — 计算入库价格"""
        return self.client.get("v2/product/compute/in_price", params={
            "shop_id": shop_id, "product_id": product_id,
            "in": in_number, "in_price": in_price,
        })

    def batch_lot_stock(self, shop_id, items, mark="扫码入库"):
        """POST v2/product/update/lotStock — 批量入库

        :param shop_id: 门店 ID
        :param items: [{"inPrice": 10, "number": 10, "productId": 104465826}, ...]
        :param mark: 入库备注
        """
        return self.client.post("v2/product/update/lotStock", json={
            "shopId": shop_id, "mark": mark,
            "data": items, "shop_id": shop_id,
        })

    # === 组合商品（SPU）===

    def save_spu(self, spu_data, retry=True):
        """POST v2/spu/save — 创建/编辑组合商品

        :param spu_data: 组合商品数据（spu_id="0" 表示新建）
        :param retry: 是否启用频率限制重试（默认 True）
        """
        if not retry:
            return self.client.post("v2/spu/save", json=spu_data)

        # 带重试的创建逻辑
        for attempt in range(RETRY_MAX_ATTEMPTS):
            resp = self.client.post("v2/spu/save", json=spu_data)
            data = resp.json()

            if data.get("error") != 0:
                msg = data.get("message", "")
                if any(kw in msg for kw in ["频繁", "稍后", "too many", "rate", "limit"]):
                    if attempt < RETRY_MAX_ATTEMPTS - 1:
                        wait_time = RETRY_BASE_DELAY * (RETRY_BACKOFF ** attempt)
                        logger.warning(f"[重试] 创建组合商品频率限制，等待 {wait_time:.1f}s 后重试 ({attempt + 1}/{RETRY_MAX_ATTEMPTS})")
                        time.sleep(wait_time)
                        continue

            return resp

        return resp

    def get_spu_detail(self, spu_id, shop_id, simple=0):
        """GET v2/spu/id — 获取组合商品详情"""
        return self.client.get("v2/spu/id", params={
            "id": spu_id, "simple": simple, "shop_id": shop_id,
        })

    def delete_spu(self, spu_id, shop_id):
        """DELETE v2/spu/del — 删除组合商品"""
        return self.client.delete(f"v2/spu/del?id={spu_id}&shop_id={shop_id}")

    # === 批量删除 ===

    def batch_delete_products(self, shop_id, product_ids, kind=6, is_del=1):
        """POST v2/Product/batch_update — 批量删除商品

        :param kind: 6 表示删除操作
        :param is_del: 1 表示确认删除
        """
        return self.client.post("v2/Product/batch_update", json={
            "shopId": shop_id, "product_ids": product_ids,
            "kind": kind, "is_del": is_del, "shop_id": shop_id,
        })
