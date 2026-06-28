# -*- coding: utf-8 -*-
"""
会员关键字 - 会员管理相关的业务关键字
"""
import time
import copy
from typing import Dict, List, Optional
from keywords.base import BaseKeywords, KeywordResult
from apis.member_api import MemberAPI
from utils.data_loader import load_yaml


class MemberKeywords(BaseKeywords):
    """会员管理操作的关键字类。"""

    def __init__(self, client=None):
        super().__init__(client)
        self.api = MemberAPI(self.client)
        self.member_data = load_yaml("member_data.yaml")

    # ========== 会员基础关键字 ==========

    def get_member_list(self, keywords: str = "", page: int = 1,
                        rfm_level: int = 0) -> KeywordResult:
        """
        获取会员列表（支持筛选）。

        用法:
            result = kw.get_member_list(keywords="Mia")
            members = result.data["members"]
        """
        resp = self.api.get_member_list(
            self.shop_id, keywords=keywords, page=page, rfm_level=rfm_level
        )
        return self.verify_success(resp, "获取会员列表")

    def get_member_by_id(self, member_id: int) -> KeywordResult:
        """
        根据 ID 获取会员详情。

        用法:
            result = kw.get_member_by_id(1020413)
            member = result.data
        """
        resp = self.api.get_member_by_id(self.shop_id, member_id)
        return self.verify_success(resp, f"获取会员 {member_id}")

    def search_member(self, keywords: str) -> KeywordResult:
        """
        按关键词搜索会员（手机号/姓名）。

        用法:
            result = kw.search_member("13698106099")
            if result and result.data["members"]:
                member = result.data["members"][0]
        """
        result = self.get_member_list(keywords=keywords)
        if result.success:
            members = result.data.get("members") if result.data else []
            if members:
                return KeywordResult(True, members, f"找到 {len(members)} 个会员")
            return KeywordResult(True, [], "未找到会员")
        return result

    # ========== 创建会员关键字 ==========

    def create_member(self, member_data: Dict = None,
                      use_template: str = "normal") -> KeywordResult:
        """
        创建新会员。

        用法:
            # 使用默认模板
            result = kw.create_member()

            # 使用指定模板
            result = kw.create_member(use_template="multi_pets")

            # 使用自定义数据
            result = kw.create_member(member_data={"name": "测试", "phone": "138..."})
        """
        if member_data is None:
            member_data = copy.deepcopy(self.member_data["new_member"][use_template])

        # 使用模板时生成唯一手机号
        if "phone" in member_data and member_data["phone"].startswith("138001"):
            member_data["phone"] = self.generate_unique_phone()

        # 确保 shop_id 存在
        member_data["shop_id"] = self.shop_id
        member_data["shopId"] = str(self.shop_id)

        resp = self.api.add_member(member_data)
        result = self.verify_success(resp, "创建会员")

        if result.success:
            member_id = result.data
            self.register_cleanup("member", member_id)
            self.set_context("last_member_id", member_id)
            self.set_context("last_member_phone", member_data.get("phone"))
            return KeywordResult(True, member_id, f"已创建会员 {member_id}")

        return result

    def create_member_with_pets(self, name: str, phone: str,
                                 pets: List[Dict]) -> KeywordResult:
        """
        创建带宠物的会员。

        用法:
            result = kw.create_member_with_pets(
                name="测试用户",
                phone="13812345678",
                pets=[{"name": "狗狗1", "speciesId": 3}]
            )
        """
        member_data = {
            "name": name,
            "phone": phone,
            "sex": 1,
            "shop_id": self.shop_id,
            "shopId": str(self.shop_id),
            "is_spending_msg": 1,
            "is_open_upgrade": 1,
            "pets": pets
        }
        return self.create_member(member_data=member_data)

    # ========== 标签关键字 ==========

    def get_default_tags(self) -> KeywordResult:
        """
        获取默认会员标签。

        用法:
            result = kw.get_default_tags()
            tags = result.data  # 标签列表
        """
        resp = self.api.get_default_tags(self.shop_id, self.store_id)
        return self.verify_success(resp, "获取默认标签")

    def create_tag(self, tag_name: str = None) -> KeywordResult:
        """
        创建新的会员标签。

        用法:
            result = kw.create_tag("VIP客户")
            tag_id = result.data
        """
        if tag_name is None:
            tag_name = f"自动标签_{int(time.time())}"

        resp = self.api.add_shop_tag(self.shop_id, self.store_id, tag_name)
        result = self.verify_success(resp, f"创建标签 '{tag_name}'")

        if result.success:
            tag_id = result.data
            self.register_cleanup("tag", tag_id)
            self.set_context("last_tag_id", tag_id)
            return KeywordResult(True, tag_id, f"已创建标签 {tag_id}")

        return result

    def create_member_with_tag(self, tag_name: str = None) -> KeywordResult:
        """
        创建标签和带该标签的会员。

        用法:
            result = kw.create_member_with_tag("高级会员")
            member_id = result.data["member_id"]
            tag_id = result.data["tag_id"]
        """
        # 创建标签
        tag_result = self.create_tag(tag_name)
        if not tag_result.success:
            return tag_result

        tag_id = tag_result.data

        # 创建带标签的会员
        member_data = copy.deepcopy(self.member_data["new_member"]["normal"])
        member_data["phone"] = self.generate_unique_phone()
        member_data["member_tags"] = str(tag_id)

        member_result = self.create_member(member_data=member_data)
        if not member_result.success:
            return member_result

        return KeywordResult(True, {
            "member_id": member_result.data,
            "tag_id": tag_id
        }, "已创建带标签的会员")

    # ========== 查询关键字 ==========

    def get_rfm_levels(self) -> KeywordResult:
        """
        获取 RFM 等级列表。

        用法:
            result = kw.get_rfm_levels()
            levels = result.data  # 8个RFM等级列表
        """
        resp = self.api.get_rfm_level_list(self.shop_id)
        return self.verify_success(resp, "获取 RFM 等级")

    def get_species_list(self) -> KeywordResult:
        """
        获取宠物品种列表。

        用法:
            result = kw.get_species_list()
            species = result.data  # 品种列表
        """
        resp = self.api.get_species_level(self.shop_id)
        return self.verify_success(resp, "获取宠物品种列表")

    def get_member_balance_log(self, member_id: int) -> KeywordResult:
        """
        获取会员余额日志。

        用法:
            result = kw.get_member_balance_log(1020413)
        """
        resp = self.api.get_balance_log(self.shop_id, self.store_id, member_id)
        return self.verify_success(resp, f"获取会员 {member_id} 的余额日志")

    def get_member_once_cards(self, member_id: int) -> KeywordResult:
        """
        获取会员次卡。

        用法:
            result = kw.get_member_once_cards(1020413)
        """
        resp = self.api.get_member_once_cards(self.shop_id, member_id)
        return self.verify_success(resp, f"获取会员 {member_id} 的次卡")

    # ========== 组合业务关键字 ==========

    def create_and_verify_member(self, member_data: Dict = None,
                                  use_template: str = "normal") -> KeywordResult:
        """
        创建会员并验证是否存在于列表中。

        用法:
            result = kw.create_and_verify_member()
            member_id = result.data["member_id"]
            member_detail = result.data["detail"]
        """
        # 步骤1: 创建会员
        create_result = self.create_member(member_data, use_template)
        if not create_result.success:
            return create_result

        member_id = create_result.data
        phone = self.get_context("last_member_phone")

        # 步骤2: 等待数据同步
        self.wait(reason="数据同步")

        # 步骤3: 搜索并验证
        search_result = self.search_member(phone)
        if not search_result.success:
            return KeywordResult(False, None, f"创建成功但搜索失败: {search_result.message}")

        if not search_result.data:
            return KeywordResult(False, None, "创建成功但未在搜索结果中找到")

        # 步骤4: 获取详情
        detail_result = self.get_member_by_id(member_id)
        if not detail_result.success:
            return KeywordResult(False, None, f"创建成功但获取详情失败: {detail_result.message}")

        return KeywordResult(True, {
            "member_id": member_id,
            "phone": phone,
            "detail": detail_result.data
        }, f"会员 {member_id} 创建并验证成功")

    def full_member_flow(self) -> KeywordResult:
        """
        执行完整的会员管理流程:
        1. 获取宠物品种列表
        2. 创建标签
        3. 创建带宠物和标签的会员
        4. 查询并验证
        5. 检查 RFM 等级

        用法:
            result = kw.full_member_flow()
            print(result.data)  # 包含所有创建的ID
        """
        results = {}

        # 步骤1: 获取品种
        species_result = self.get_species_list()
        if not species_result.success:
            return species_result
        results["species_count"] = len(species_result.data)

        # 步骤2: 创建标签
        tag_result = self.create_tag()
        if not tag_result.success:
            return tag_result
        results["tag_id"] = tag_result.data

        # 步骤3: 创建带标签的会员
        member_data = copy.deepcopy(self.member_data["new_member"]["normal"])
        member_data["phone"] = self.generate_unique_phone()
        member_data["member_tags"] = str(tag_result.data)

        # 使用第一个狗品种作为宠物
        if species_result.data and species_result.data[0].get("list"):
            member_data["pets"][0]["speciesId"] = species_result.data[0]["list"][0]["species_id"]

        create_result = self.create_and_verify_member(member_data=member_data)
        if not create_result.success:
            return create_result
        results["member_id"] = create_result.data["member_id"]
        results["phone"] = create_result.data["phone"]

        # 步骤4: 检查 RFM 等级
        rfm_result = self.get_rfm_levels()
        if not rfm_result.success:
            return rfm_result
        results["rfm_level_count"] = len(rfm_result.data)

        return KeywordResult(True, results, "会员完整流程执行完成")
