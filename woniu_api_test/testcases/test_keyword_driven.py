# -*- coding: utf-8 -*-
"""
关键字驱动测试 - 使用关键字框架编写更简洁的测试

优点:
1. 代码量减少 60-70%
2. 可读性更好
3. 维护更方便
4. 业务逻辑可复用
"""
import logging
import pytest
from keywords.member_keywords import MemberKeywords
from keywords.product_keywords import ProductKeywords
from utils.data_loader import load_yaml

logger = logging.getLogger(__name__)
member_data = load_yaml("member_data.yaml")


@pytest.fixture(scope="module")
def member_kw(api_client):
    """会员关键字实例。"""
    return MemberKeywords(api_client)


@pytest.fixture(scope="module")
def product_kw(api_client):
    """商品关键字实例。"""
    return ProductKeywords(api_client)


# ╔══════════════════════════════════════════════════════════════╗
# ║                    会员关键字驱动测试                          ║
# ╚══════════════════════════════════════════════════════════════╝

@pytest.mark.unit
class TestMemberKeywords:
    """【单元】会员关键字测试。"""

    def test_get_member_list(self, member_kw):
        """获取会员列表"""
        result = member_kw.get_member_list()
        assert result.success, result.message

    def test_search_member(self, member_kw):
        """按关键词搜索会员"""
        result = member_kw.search_member("Mia")
        assert result.success, result.message

    def test_get_rfm_levels(self, member_kw):
        """获取 RFM 等级列表"""
        result = member_kw.get_rfm_levels()
        assert result.success, result.message
        assert len(result.data) == 8

    def test_get_species_list(self, member_kw):
        """获取宠物品种列表"""
        result = member_kw.get_species_list()
        assert result.success, result.message
        assert len(result.data) > 0

    def test_get_default_tags(self, member_kw):
        """获取默认会员标签"""
        result = member_kw.get_default_tags()
        assert result.success, result.message

    def test_create_tag(self, member_kw):
        """创建新标签"""
        result = member_kw.create_tag("Test Tag")
        assert result.success, result.message
        assert isinstance(result.data, int)


@pytest.mark.integration
class TestMemberKeywordsIntegration:
    """【集成】会员关键字测试。"""

    def test_create_member(self, member_kw):
        """创建会员"""
        result = member_kw.create_member()
        assert result.success, result.message
        assert isinstance(result.data, int)

    def test_create_and_verify_member(self, member_kw):
        """创建会员并验证是否存在"""
        result = member_kw.create_and_verify_member()
        assert result.success, result.message
        assert "member_id" in result.data
        assert "detail" in result.data

    def test_create_member_with_tag(self, member_kw):
        """同时创建标签和会员"""
        result = member_kw.create_member_with_tag("Premium User")
        assert result.success, result.message
        assert "member_id" in result.data
        assert "tag_id" in result.data


@pytest.mark.scenario
class TestMemberKeywordsScenario:
    """【场景】会员关键字测试。"""

    def test_full_member_flow(self, member_kw):
        """
        完整会员管理流程（单个关键字实现）。

        用一个关键字调用替代 100+ 行代码:
        1. 获取品种列表
        2. 创建标签
        3. 创建带宠物和标签的会员
        4. 查询并验证
        5. 检查 RFM 等级
        """
        result = member_kw.full_member_flow()
        assert result.success, result.message

        # 验证所有步骤已完成
        data = result.data
        assert data["species_count"] > 0, "应有品种数据"
        assert data["tag_id"] > 0, "应成功创建标签"
        assert data["member_id"] > 0, "应成功创建会员"
        assert data["rfm_level_count"] == 8, "应有 8 个 RFM 等级"

        logger.info(f"[完整流程] 创建会员 {data['member_id']}，标签 {data['tag_id']}")


# ╔══════════════════════════════════════════════════════════════╗
# ║                    商品关键字驱动测试                          ║
# ╚══════════════════════════════════════════════════════════════╝

@pytest.mark.unit
class TestProductKeywords:
    """【单元】商品关键字测试。"""

    def test_get_product_list(self, product_kw):
        """获取商品列表"""
        result = product_kw.get_product_list()
        assert result.success, result.message

    def test_get_sku_list(self, product_kw):
        """获取 SKU 列表"""
        result = product_kw.get_sku_list()
        assert result.success, result.message


@pytest.mark.integration
class TestProductKeywordsIntegration:
    """【集成】商品关键字测试。"""

    def test_create_and_stock_product(self, product_kw):
        """
        创建商品并入库 - 替代 30+ 行代码。

        传统写法:
            resp = product_api.add_sku(data)
            assert resp.json()["error"] == 0
            product_id = resp.json()["data"]["product_id"]
            time.sleep(0.5)
            resp = product_api.update_stocks(shop_id, product_id, 10, "mark")
            assert resp.json()["error"] == 0
            # ... 清理代码

        关键字写法:
        """
        result = product_kw.create_and_stock_product(number=10)
        assert result.success, result.message
        assert result.data["product_id"] > 0
        assert result.data["stock_number"] == 10

        # 清理数据
        product_kw.cleanup_products()

    def test_create_multiple_products(self, product_kw):
        """批量创建商品并入库"""
        result = product_kw.create_multiple_products(count=2, stock_each=5)
        assert result.success, result.message
        assert len(result.data["product_ids"]) == 2

        # 清理数据
        product_kw.cleanup_products()


# ╔══════════════════════════════════════════════════════════════╗
# ║                    组合关键字场景测试                          ║
# ╚══════════════════════════════════════════════════════════════╝

@pytest.mark.scenario
class TestCombinedKeywordScenarios:
    """【场景】多关键字组合的复杂场景测试。"""

    def test_member_and_product_flow(self, member_kw, product_kw):
        """
        组合业务流程:
        1. 创建会员
        2. 创建商品并入库
        3. 验证两者都存在

        传统代码: 150+ 行
        关键字驱动: 20 行
        """
        # 步骤1: 创建并验证会员
        member_result = member_kw.create_and_verify_member()
        assert member_result.success, f"会员创建失败: {member_result.message}"
        member_id = member_result.data["member_id"]

        # 步骤2: 创建商品并入库
        product_result = product_kw.create_and_stock_product(number=15)
        assert product_result.success, f"商品创建失败: {product_result.message}"
        product_id = product_result.data["product_id"]

        # 步骤3: 验证会员详情
        detail_result = member_kw.get_member_by_id(member_id)
        assert detail_result.success

        # 步骤4: 验证商品列表
        list_result = product_kw.get_product_list()
        assert list_result.success

        logger.info(f"[组合流程] 会员 {member_id}，商品 {product_id}")

        # 清理数据
        product_kw.cleanup_products()


# ╔══════════════════════════════════════════════════════════════╗
# ║                    数据驱动关键字测试                          ║
# ╚══════════════════════════════════════════════════════════════╝

@pytest.mark.unit
class TestDataDrivenKeywords:
    """【单元】数据驱动的关键字测试。"""

    @pytest.mark.parametrize("keywords", ["Mia", "test", "13698106099"],
                             ids=["按姓名", "按关键词", "按手机号"])
    def test_search_member_parametrized(self, member_kw, keywords):
        """参数化搜索会员"""
        result = member_kw.search_member(keywords)
        assert result.success, result.message

    @pytest.mark.parametrize("rfm_info", [{"level": 0, "title": "全部"}] + member_data["rfm_levels"],
                             ids=["全部"] + [l["title"] for l in member_data["rfm_levels"]])
    def test_filter_member_by_rfm(self, member_kw, rfm_info):
        """按 RFM 等级筛选会员"""
        result = member_kw.get_member_list(rfm_level=rfm_info["level"])
        assert result.success, result.message
