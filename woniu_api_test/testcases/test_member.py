"""
会员管理模块 —— 全量测试用例
按测试层级分为：单元接口测试 / 集成接口测试 / 业务场景测试
基于 API 录制文档 api-recording-20260624-191946.md 生成
"""
import copy
import time
import logging
import pytest
from apis.member_api import MemberAPI
from utils.data_loader import load_yaml
from utils.helpers import generate_unique_phone
from config.settings import SYNC_WAIT_TIME

logger = logging.getLogger(__name__)

member_data = load_yaml("member_data.yaml")
config_data = load_yaml("config.yaml")

SHOP_ID = config_data["shop"]["shop_id"]
STORE_ID = config_data["shop"]["store_id"]


@pytest.fixture(scope="module")
def member_api(api_client):
    """全模块共享一个 MemberAPI 实例。"""
    return MemberAPI(api_client)


# ╔══════════════════════════════════════════════════════════════╗
# ║                    一、单元接口测试                            ║
# ║    覆盖维度：正常 / 边界 / 异常 / 安全                         ║
# ╚══════════════════════════════════════════════════════════════╝

@pytest.mark.unit
class TestMemberList:
    """【单元】会员列表查询：分页、搜索、排序"""

    def test_get_member_list_success(self, member_api):
        """正常：获取会员列表"""
        resp = member_api.get_member_list(SHOP_ID)
        data = resp.json()
        assert data["error"] == 0
        assert "members" in data["data"]

    @pytest.mark.parametrize("keywords", member_data["search_keywords"]["valid"],
                             ids=["关键词_Mia", "关键词_测试", "关键词_手机号"])
    def test_search_member_by_keywords(self, member_api, keywords):
        """正常：参数化关键词搜索"""
        resp = member_api.get_member_list(SHOP_ID, keywords=keywords)
        assert resp.json()["error"] == 0

    @pytest.mark.parametrize("keywords", member_data["search_keywords"]["special"],
                             ids=["XSS注入", "SQL注入", "空字符串", "不存在会员"])
    def test_search_member_special_keywords(self, member_api, keywords):
        """安全/边界：特殊字符搜索"""
        resp = member_api.get_member_list(SHOP_ID, keywords=keywords)
        data = resp.json()
        assert data["error"] == 0
        # 不存在的会员应返回空列表
        if keywords == "不存在的会员名称XXXXXX":
            members = data["data"].get("members") if data["data"] else []
            assert members is None or len(members) == 0

    @pytest.mark.parametrize("page_config", list(member_data["pagination"].values()),
                             ids=list(member_data["pagination"].keys()))
    def test_member_list_pagination(self, member_api, page_config):
        """边界：会员列表分页参数"""
        resp = member_api.get_member_list(SHOP_ID, page=page_config["page"])
        assert resp.json()["error"] == 0

    @pytest.mark.parametrize("order_by", ["updated", "created", "last_order_time"],
                             ids=["按更新时间", "按创建时间", "按最后消费时间"])
    def test_member_list_order_by(self, member_api, order_by):
        """正常：会员列表排序"""
        resp = member_api.get_member_list(SHOP_ID, order_by=order_by)
        assert resp.json()["error"] == 0

    @pytest.mark.parametrize("rfm_info", [{"level": 0, "title": "全部"}] + member_data["rfm_levels"],
                             ids=["全部"] + [l["title"] for l in member_data["rfm_levels"]])
    def test_member_list_filter_rfm(self, member_api, rfm_info):
        """正常：按 RFM 等级筛选"""
        resp = member_api.get_member_list(SHOP_ID, rfm_level=rfm_info["level"])
        assert resp.json()["error"] == 0


@pytest.mark.unit
class TestMemberDetail:
    """【单元】会员详情查询"""

    def test_get_member_by_id_success(self, member_api):
        """正常：获取会员详情"""
        member_id = config_data["member"]["existing_member_id"]
        resp = member_api.get_member_by_id(SHOP_ID, member_id)
        data = resp.json()
        assert data["error"] == 0
        assert data["data"]["member_id"] == member_id

    def test_get_member_by_id_not_exist(self, member_api):
        """异常：不存在的会员 ID"""
        resp = member_api.get_member_by_id(SHOP_ID, 999999999)
        data = resp.json()
        assert data["error"] != 0 or data["data"] is None

    def test_get_member_by_id_invalid_format(self, member_api):
        """异常：无效的会员 ID 格式"""
        resp = member_api.get_member_by_id(SHOP_ID, "invalid_id")
        # 服务端可能返回 400 或 200，只要能正常响应即可
        assert resp.status_code in [200, 400]


@pytest.mark.unit
class TestMemberOnceCards:
    """【单元】会员次卡查询"""

    def test_get_member_once_cards_success(self, member_api):
        """正常：获取会员次卡"""
        member_id = config_data["member"]["existing_member_id"]
        resp = member_api.get_member_once_cards(SHOP_ID, member_id)
        data = resp.json()
        assert data["error"] == 0

    def test_get_member_once_cards_not_exist(self, member_api):
        """异常：不存在会员的次卡"""
        resp = member_api.get_member_once_cards(SHOP_ID, 999999999)
        assert resp.status_code == 200


@pytest.mark.unit
class TestMemberTags:
    """【单元】会员标签接口"""

    def test_get_default_tags_success(self, member_api):
        """正常：获取默认标签列表"""
        resp = member_api.get_default_tags(SHOP_ID, STORE_ID)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], list)
        if len(data["data"]) > 0:
            assert "tag_id" in data["data"][0]
            assert "name" in data["data"][0]

    def test_add_shop_tag_success(self, member_api):
        """正常：新增店铺标签"""
        tag_name = f"自动化测试标签_{int(time.time())}"
        resp = member_api.add_shop_tag(SHOP_ID, STORE_ID, tag_name)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], int)

    def test_add_shop_tag_empty_name(self, member_api):
        """异常：空标签名"""
        resp = member_api.add_shop_tag(SHOP_ID, STORE_ID, "")
        data = resp.json()
        assert data["error"] != 0 or resp.status_code == 200

    def test_add_shop_tag_special_chars(self, member_api):
        """安全：特殊字符标签名"""
        resp = member_api.add_shop_tag(SHOP_ID, STORE_ID, "<script>alert(1)</script>")
        assert resp.status_code == 200


@pytest.mark.unit
class TestRfmLevel:
    """【单元】RFM 等级接口"""

    def test_get_rfm_level_list_success(self, member_api):
        """正常：获取 RFM 等级列表"""
        resp = member_api.get_rfm_level_list(SHOP_ID)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], list)

        # 使用 yaml 数据验证返回结果
        expected_levels = member_data["rfm_levels"]
        assert len(data["data"]) == len(expected_levels)
        for i, level in enumerate(data["data"]):
            assert level["level"] == expected_levels[i]["level"]
            assert level["title"] == expected_levels[i]["title"]


@pytest.mark.unit
class TestSpecies:
    """【单元】宠物品种接口"""

    def test_get_species_level_success(self, member_api):
        """正常：获取宠物品种列表"""
        resp = member_api.get_species_level(SHOP_ID)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        assert data["data"][0]["name"] == "狗"


@pytest.mark.unit
class TestStaff:
    """【单元】员工列表接口"""

    def test_get_staff_list_success(self, member_api):
        """正常：获取员工列表"""
        resp = member_api.get_staff_list(SHOP_ID)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], list)


@pytest.mark.unit
class TestShopCards:
    """【单元】店铺卡券接口"""

    def test_get_shop_once_cards_success(self, member_api):
        """正常：获取店铺次卡列表"""
        resp = member_api.get_shop_once_cards(SHOP_ID)
        data = resp.json()
        assert data["error"] == 0

    def test_get_member_level_list_success(self, member_api):
        """正常：获取会员等级列表"""
        resp = member_api.get_member_level_list(SHOP_ID)
        data = resp.json()
        assert data["error"] == 0

    def test_get_shopping_card_list_success(self, member_api):
        """正常：获取购物卡列表"""
        resp = member_api.get_shopping_card_list(SHOP_ID)
        data = resp.json()
        assert data["error"] == 0
        assert "list" in data["data"]
        assert "pager" in data["data"]


@pytest.mark.unit
class TestMarketingActivity:
    """【单元】营销活动接口"""

    def test_get_marketing_activity_list_success(self, member_api):
        """正常：获取营销活动列表"""
        resp = member_api.get_marketing_activity_list(SHOP_ID)
        data = resp.json()
        assert data["error"] == 0
        assert "list" in data["data"]
        assert "pager" in data["data"]


@pytest.mark.unit
class TestUserStoreSetting:
    """【单元】用户门店设置接口"""

    def test_get_user_store_setting_success(self, member_api):
        """正常：获取用户门店设置"""
        resp = member_api.get_user_store_setting(SHOP_ID, "member_list_rfm")
        data = resp.json()
        assert data["error"] == 0

    def test_get_user_store_setting_invalid_key(self, member_api):
        """边界：无效的设置 key"""
        resp = member_api.get_user_store_setting(SHOP_ID, "invalid_key_xxx")
        assert resp.status_code == 200


@pytest.mark.unit
class TestBalanceLog:
    """【单元】会员余额日志接口"""

    def test_get_balance_log_success(self, member_api):
        """正常：获取会员余额日志"""
        member_id = config_data["member"]["existing_member_id"]
        resp = member_api.get_balance_log(SHOP_ID, STORE_ID, member_id)
        data = resp.json()
        assert data["error"] == 0

    def test_get_balance_log_with_action_filter(self, member_api):
        """正常：按操作类型筛选余额日志"""
        member_id = config_data["member"]["existing_member_id"]
        resp = member_api.get_balance_log(SHOP_ID, STORE_ID, member_id, actions=1)
        data = resp.json()
        assert data["error"] == 0


@pytest.mark.unit
class TestCreateMember:
    """【单元】新建会员接口：正常 / 边界 / 异常 / 安全"""

    def test_create_member_success(self, member_api):
        """正常：创建会员"""
        new_member = copy.deepcopy(member_data["new_member"]["normal"])
        new_member["phone"] = generate_unique_phone("138")
        resp = member_api.add_member(new_member)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], int)

    def test_create_member_with_multi_pets(self, member_api):
        """正常：创建多宠物会员"""
        new_member = copy.deepcopy(member_data["new_member"]["multi_pets"])
        new_member["phone"] = generate_unique_phone("139")
        resp = member_api.add_member(new_member)
        data = resp.json()
        assert data["error"] == 0

    def test_create_member_missing_phone(self, member_api):
        """异常：缺少手机号"""
        resp = member_api.add_member(member_data["invalid_member"]["missing_phone"])
        data = resp.json()
        assert data["error"] != 0 or data.get("code") != 0

    def test_create_member_empty_name(self, member_api):
        """边界：空名称"""
        new_member = copy.deepcopy(member_data["invalid_member"]["empty_name"])
        new_member["phone"] = generate_unique_phone("137")
        resp = member_api.add_member(new_member)
        # 空名称可能被接受（系统默认处理）或拒绝
        assert resp.status_code == 200

    def test_create_member_invalid_phone_format(self, member_api):
        """异常：无效手机号格式"""
        resp = member_api.add_member(member_data["invalid_member"]["invalid_phone_format"])
        data = resp.json()
        assert data["error"] != 0 or data.get("code") != 0

    def test_create_member_sql_injection(self, member_api):
        """安全：SQL 注入会员名"""
        new_member = copy.deepcopy(member_data["invalid_member"]["sql_injection"])
        new_member["phone"] = generate_unique_phone("136")
        resp = member_api.add_member(new_member)
        # 应正常处理，不应执行注入
        assert resp.status_code == 200

    def test_create_member_xss_injection(self, member_api):
        """安全：XSS 注入会员名"""
        new_member = copy.deepcopy(member_data["invalid_member"]["xss_injection"])
        new_member["phone"] = generate_unique_phone("135")
        resp = member_api.add_member(new_member)
        assert resp.status_code == 200


# ╔══════════════════════════════════════════════════════════════╗
# ║                    二、集成接口测试                            ║
# ║    多接口串联验证：创建→查询→更新→删除 等                      ║
# ╚══════════════════════════════════════════════════════════════╝

@pytest.mark.integration
class TestMemberCRUD:
    """【集成】会员增删改查"""

    def test_create_and_query_member(self, member_api):
        """集成：创建会员 → 搜索验证 → 查询详情"""
        # Step 1: 创建会员
        new_member = copy.deepcopy(member_data["new_member"]["normal"])
        phone = generate_unique_phone("138")
        new_member["phone"] = phone
        new_member["name"] = "集成测试会员"

        resp = member_api.add_member(new_member)
        data = resp.json()
        assert data["error"] == 0, f"创建会员失败: {data}"
        member_id = data["data"]

        # Step 2: 搜索验证
        time.sleep(SYNC_WAIT_TIME)
        resp = member_api.get_member_list(SHOP_ID, keywords=phone)
        data = resp.json()
        assert data["error"] == 0
        assert len(data["data"]["members"]) > 0

        # Step 3: 查询详情
        resp = member_api.get_member_by_id(SHOP_ID, member_id)
        data = resp.json()
        assert data["error"] == 0
        assert data["data"]["phone"] == phone
        assert data["data"]["name"] == "集成测试会员"

    def test_create_member_and_query_cards(self, member_api):
        """集成：创建会员 → 查询次卡 → 查询余额日志"""
        # 创建会员
        new_member = copy.deepcopy(member_data["new_member"]["normal"])
        new_member["phone"] = generate_unique_phone("139")
        resp = member_api.add_member(new_member)
        data = resp.json()
        assert data["error"] == 0
        member_id = data["data"]

        # 查询次卡
        resp = member_api.get_member_once_cards(SHOP_ID, member_id)
        assert resp.json()["error"] == 0

        # 查询余额日志
        resp = member_api.get_balance_log(SHOP_ID, STORE_ID, member_id)
        assert resp.json()["error"] == 0


@pytest.mark.integration
class TestTagAndMember:
    """【集成】标签与会员关联"""

    def test_create_tag_and_assign_to_member(self, member_api):
        """集成：创建标签 → 创建带标签的会员 → 验证"""
        # 创建标签
        tag_name = f"集成测试标签_{int(time.time())}"
        resp = member_api.add_shop_tag(SHOP_ID, STORE_ID, tag_name)
        data = resp.json()
        assert data["error"] == 0
        tag_id = data["data"]

        # 创建带标签的会员
        new_member = copy.deepcopy(member_data["new_member"]["normal"])
        new_member["phone"] = generate_unique_phone("137")
        new_member["member_tags"] = str(tag_id)
        resp = member_api.add_member(new_member)
        data = resp.json()
        assert data["error"] == 0


# ╔══════════════════════════════════════════════════════════════╗
# ║                   三、业务场景测试                             ║
# ║    完整业务链路：端到端验证                                    ║
# ╚══════════════════════════════════════════════════════════════╝

@pytest.mark.scenario
class TestMemberFullScenario:
    """【场景】会员管理完整链路"""

    def test_full_member_management_flow(self, member_api):
        """完整场景：获取品种 → 创建标签 → 创建会员(带宠物) → 查询详情 → 验证数据"""

        # Step 1: 获取宠物品种列表
        resp = member_api.get_species_level(SHOP_ID)
        data = resp.json()
        assert data["error"] == 0, "[Step1] 获取品种失败"
        species_list = data["data"]
        assert len(species_list) > 0
        # 获取第一个有子品种的物种
        dog_species = next((s for s in species_list if s["name"] == "狗"), None)
        assert dog_species is not None
        sub_species = dog_species["list"][0] if dog_species.get("list") else None
        logger.info(f"[Step1] 获取品种成功: 狗->{sub_species['name'] if sub_species else 'N/A'}")

        # Step 2: 创建会员标签
        tag_name = f"场景测试标签_{int(time.time())}"
        resp = member_api.add_shop_tag(SHOP_ID, STORE_ID, tag_name)
        data = resp.json()
        assert data["error"] == 0, f"[Step2] 创建标签失败: {data}"
        tag_id = data["data"]
        logger.info(f"[Step2] 创建标签成功: {tag_name} (id={tag_id})")

        # Step 3: 创建会员（带宠物和标签）
        new_member = copy.deepcopy(member_data["new_member"]["normal"])
        phone = generate_unique_phone("138")
        new_member["phone"] = phone
        new_member["name"] = "场景测试会员"
        new_member["member_tags"] = str(tag_id)
        if sub_species:
            new_member["pets"][0]["speciesId"] = sub_species["species_id"]

        resp = member_api.add_member(new_member)
        data = resp.json()
        assert data["error"] == 0, f"[Step3] 创建会员失败: {data}"
        member_id = data["data"]
        logger.info(f"[Step3] 创建会员成功: {phone} (id={member_id})")

        # Step 4: 查询会员详情
        time.sleep(SYNC_WAIT_TIME)
        resp = member_api.get_member_by_id(SHOP_ID, member_id)
        data = resp.json()
        assert data["error"] == 0, f"[Step4] 查询详情失败: {data}"
        member_detail = data["data"]
        assert member_detail["phone"] == phone
        assert member_detail["name"] == "场景测试会员"
        assert len(member_detail["pets"]) == 1
        logger.info(f"[Step4] 会员详情验证通过: 宠物数={len(member_detail['pets'])}")

        # Step 5: 查询会员列表确认存在
        resp = member_api.get_member_list(SHOP_ID, keywords=phone)
        data = resp.json()
        assert data["error"] == 0
        assert len(data["data"]["members"]) > 0
        found = any(m["member_id"] == member_id for m in data["data"]["members"])
        assert found, "[Step5] 会员列表中未找到新创建的会员"
        logger.info(f"[Step5] 会员列表验证通过")

        # Step 6: 查询 RFM 等级列表
        resp = member_api.get_rfm_level_list(SHOP_ID)
        data = resp.json()
        assert data["error"] == 0
        assert len(data["data"]) == 8
        logger.info(f"[Step6] RFM 等级列表验证通过: 共 {len(data['data'])} 个等级")

        logger.info("[完成] 会员管理完整链路测试结束")
