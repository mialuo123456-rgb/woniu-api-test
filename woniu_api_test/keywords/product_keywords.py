# -*- coding: utf-8 -*-
"""
商品关键字 - 商品管理相关的业务关键字
"""
import time
import copy
from typing import Dict, List, Optional
from keywords.base import BaseKeywords, KeywordResult
from apis.product_api import ProductAPI
from utils.data_loader import load_yaml


class ProductKeywords(BaseKeywords):
    """商品管理操作的关键字类。"""

    def __init__(self, client=None):
        super().__init__(client)
        self.api = ProductAPI(self.client)
        self.product_data = load_yaml("product_data.yaml")

    # ========== 商品基础关键字 ==========

    def get_product_list(self, keywords: str = "", page: int = 1,
                         limit: int = 15) -> KeywordResult:
        """
        获取商品列表。

        用法:
            result = kw.get_product_list(keywords="猫粮")
        """
        resp = self.api.get_spu_list(self.shop_id, page=page, limit=limit, keywords=keywords)
        return self.verify_success(resp, "获取商品列表")

    def get_sku_list(self, page: int = 1) -> KeywordResult:
        """
        获取 SKU 列表。

        用法:
            result = kw.get_sku_list()
        """
        resp = self.api.get_sku_list(self.shop_id, page=page)
        return self.verify_success(resp, "获取 SKU 列表")

    # ========== 创建商品关键字 ==========

    def create_product(self, product_data: Dict = None) -> KeywordResult:
        """
        创建新商品。

        用法:
            result = kw.create_product()
            product_id = result.data
        """
        if product_data is None:
            product_data = copy.deepcopy(self.product_data["product"]["new_sku"])

        resp = self.api.add_sku(product_data)
        result = self.verify_success(resp, "创建商品")

        if result.success:
            product_id = result.data.get("product_id")
            self.register_cleanup("product", product_id)
            self.set_context("last_product_id", product_id)
            return KeywordResult(True, product_id, f"已创建商品 {product_id}")

        return result

    def stock_in_product(self, product_id: int, number: int = 10,
                         mark: str = "自动测试入库") -> KeywordResult:
        """
        商品入库（增加库存）。

        用法:
            result = kw.stock_in_product(product_id, number=20)
        """
        resp = self.api.update_stocks(self.shop_id, product_id, number, mark)
        result = self.verify_success(resp, f"入库 {number} 件")

        if result.success:
            return KeywordResult(True, {"product_id": product_id, "number": number},
                               f"已为商品 {product_id} 入库 {number} 件")
        return result

    def batch_stock_in(self, items: List[Dict]) -> KeywordResult:
        """
        批量商品入库。

        用法:
            result = kw.batch_stock_in([
                {"productId": 123, "number": 10, "inPrice": 10},
                {"productId": 456, "number": 20, "inPrice": 15}
            ])
        """
        resp = self.api.batch_lot_stock(self.shop_id, items, mark="自动批量入库")
        return self.verify_success(resp, f"批量入库 {len(items)} 个商品")

    # ========== 删除商品关键字 ==========

    def delete_product(self, product_id: int) -> KeywordResult:
        """
        删除商品。

        用法:
            result = kw.delete_product(123)
        """
        resp = self.api.delete_by_ids(self.shop_id, product_id)
        return self.verify_success(resp, f"删除商品 {product_id}")

    def delete_products(self, product_ids: List[int]) -> KeywordResult:
        """
        批量删除商品。

        用法:
            result = kw.delete_products([123, 456, 789])
        """
        resp = self.api.batch_delete_products(self.shop_id, product_ids)
        return self.verify_success(resp, f"删除 {len(product_ids)} 个商品")

    # ========== 组合业务关键字 ==========

    def create_and_stock_product(self, number: int = 10,
                                  product_data: Dict = None) -> KeywordResult:
        """
        创建商品并入库。

        用法:
            result = kw.create_and_stock_product(number=20)
            product_id = result.data["product_id"]
        """
        # 步骤1: 创建商品
        create_result = self.create_product(product_data)
        if not create_result.success:
            return create_result

        product_id = create_result.data

        # 步骤2: 等待创建完成
        self.wait(reason="商品创建同步")

        # 步骤3: 入库
        stock_result = self.stock_in_product(product_id, number)
        if not stock_result.success:
            # 失败时清理
            self.delete_product(product_id)
            return stock_result

        return KeywordResult(True, {
            "product_id": product_id,
            "stock_number": number
        }, f"已创建并入库商品 {product_id}")

    def create_multiple_products(self, count: int = 2,
                                  stock_each: int = 10) -> KeywordResult:
        """
        批量创建商品并入库。

        用法:
            result = kw.create_multiple_products(count=3, stock_each=20)
            product_ids = result.data["product_ids"]
        """
        product_ids = []

        for i in range(count):
            result = self.create_and_stock_product(number=stock_each)
            if not result.success:
                # 清理已创建的商品
                if product_ids:
                    self.delete_products(product_ids)
                return result
            product_ids.append(result.data["product_id"])
            self.wait(reason=f"创建第 {i+1}/{count} 个商品")

        return KeywordResult(True, {
            "product_ids": product_ids,
            "count": count,
            "stock_each": stock_each
        }, f"已创建 {count} 个商品")

    def cleanup_products(self) -> KeywordResult:
        """
        清理所有已注册的商品。

        用法:
            kw.cleanup_products()
        """
        cleanups = self.get_cleanups("product")
        if not cleanups:
            return KeywordResult(True, [], "无需清理的商品")

        product_ids = [c["id"] for c in cleanups]
        result = self.delete_products(product_ids)

        # 清除清理注册表
        all_cleanups = self.get_context("_cleanups", [])
        self.set_context("_cleanups", [c for c in all_cleanups if c["type"] != "product"])

        return result
