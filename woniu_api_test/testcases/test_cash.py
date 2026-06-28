"""
收银台模块 —— 全量测试用例（整合版）
按测试层级分为：单元接口测试 / 集成接口测试 / 业务场景测试
"""
import logging
import pytest
from apis.cash_api import CashAPI
from apis.member_api import MemberAPI
from apis.product_api import ProductAPI
from utils.data_loader import load_yaml

logger = logging.getLogger(__name__)
config = load_yaml("config.yaml")
cash_data = load_yaml("cash_data.yaml")
product_data = load_yaml("product_data.yaml")


@pytest.fixture(scope="module")
def cash_api(api_client):
    return CashAPI(api_client)


@pytest.fixture(scope="module")
def member_api(api_client):
    return MemberAPI(api_client)


@pytest.fixture(scope="module")
def product_api(api_client):
    return ProductAPI(api_client)


# ╔══════════════════════════════════════════════════════════════╗
# ║                    一、单元接口测试                            ║
# ║    覆盖维度：正常 / 边界 / 异常 / 安全                         ║
# ╚══════════════════════════════════════════════════════════════╝

@pytest.mark.unit
class TestCashCategory:
    """【单元】收银台分类与商品列表"""

    def test_get_cash_category_success(self, cash_api, shop_id):
        """正常：收银台商品分类"""
        resp = cash_api.get_cash_category(shop_id)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], list)

    @pytest.mark.parametrize("keywords", ["", "测试", "皇家", "猫粮"],
                             ids=["空关键词", "搜索测试", "搜索皇家", "搜索猫粮"])
    def test_get_cash_list(self, cash_api, shop_id, keywords):
        """正常：参数化多关键词搜索"""
        resp = cash_api.get_cash_list(shop_id, keywords=keywords)
        assert resp.json()["error"] == 0

    @pytest.mark.parametrize("page", [1, 2, 0, 9999],
                             ids=["第1页", "第2页", "page=0", "page=9999超尾页"])
    def test_cash_list_pagination(self, cash_api, shop_id, page):
        """边界：分页参数"""
        resp = cash_api.get_cash_list(shop_id, page=page)
        assert resp.json()["error"] == 0

    def test_cash_list_xss_keywords(self, cash_api, shop_id):
        """安全：XSS 关键词搜索"""
        resp = cash_api.get_cash_list(shop_id, keywords="<img src=x onerror=alert(1)>")
        assert resp.json()["error"] == 0


@pytest.mark.unit
@pytest.mark.usefixtures("clean_cart")
class TestCart:
    """【单元】购物车操作：正常 / 边界 / 异常"""

    def test_get_cart_list_empty(self, cash_api, shop_id):
        """正常：获取空购物车列表"""
        cash_api.change_member(shop_id, member_id=-1)
        resp = cash_api.get_cart_list(shop_id)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], dict)
        assert "total_num" in data["data"]
        assert "total_price" in data["data"]

    def test_get_cart_count(self, cash_api, shop_id):
        """正常：购物车数量"""
        resp = cash_api.get_cart_count(shop_id)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], int)

    def test_change_member_default(self, cash_api, shop_id):
        """正常：切换非会员"""
        resp = cash_api.change_member(shop_id, member_id=-1)
        data = resp.json()
        assert data["error"] == 0
        assert data["data"]["member_id"] == -1
        assert data["data"]["total_num"] == 0
        assert data["data"]["total_price"] == 0

    def test_change_member_non_existent(self, cash_api, shop_id):
        """异常：切换到不存在的会员"""
        resp = cash_api.change_member(shop_id, member_id=config["member"]["non_existent_member_id"])
        assert resp.status_code == 200

    def test_add_to_cart_invalid_product(self, cash_api, shop_id):
        """异常：加购不存在的商品"""
        resp = cash_api.add_to_cart(shop_id, product_id=999999999, num=1)
        data = resp.json()
        assert data["error"] != 0

    def test_add_to_cart_zero_num(self, cash_api, shop_id):
        """边界：加购数量为0"""
        resp = cash_api.add_to_cart(shop_id, product_id=1, num=0)
        data = resp.json()
        assert data["error"] != 0 or data["data"]["total_num"] == 0

    def test_add_to_cart_negative_num(self, cash_api, shop_id):
        """异常：加购负数数量"""
        resp = cash_api.add_to_cart(shop_id, product_id=1, num=-5)
        data = resp.json()
        assert data["error"] != 0


@pytest.mark.unit
class TestPayAndOrder:
    """【单元】支付方式与订单"""

    def test_get_pay_way_list(self, cash_api, shop_id):
        """正常：获取支付方式列表"""
        resp = cash_api.get_pay_way_list(shop_id)
        data = resp.json()
        assert data["error"] == 0
        pay_list = data["data"]["other_pay_way_list"]
        assert isinstance(pay_list, list)
        assert len(pay_list) > 0
        pay = pay_list[0]
        assert "name" in pay
        assert "pay_way" in pay
        assert isinstance(pay["pay_way"], int)

    def test_build_order_empty_cart(self, cash_api, shop_id):
        """异常：空购物车下单"""
        cash_api.change_member(shop_id, member_id=-1)
        resp = cash_api.build_order(
            shop_id,
            pay_ways=[{"way": config["pay_way"]["cash"], "price": 0}],
            price=0
        )
        data = resp.json()
        assert data["error"] != 0

    def test_build_order_negative_price(self, cash_api, shop_id):
        """异常：负数金额下单"""
        resp = cash_api.build_order(
            shop_id,
            pay_ways=[{"way": config["pay_way"]["cash"], "price": -100}],
            price=-100
        )
        data = resp.json()
        assert data["error"] != 0


@pytest.mark.unit
class TestCashDict:
    """【单元】收银台字典接口：宠物种类 / 微信二维码"""

    def test_get_species_list(self, cash_api, shop_id):
        """正常：宠物种类"""
        resp = cash_api.get_species_list(shop_id)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], list)
        if len(data["data"]) > 0:
            species = data["data"][0]
            assert "species_id" in species
            assert "name" in species

    def test_get_wechat_qr(self, cash_api, shop_id):
        """正常：微信二维码"""
        resp = cash_api.get_wechat_qr(shop_id)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], str)
        assert data["data"].startswith("http")


@pytest.mark.unit
class TestMemberQuery:
    """【单元】会员接口：列表 / 详情 / 次卡 / 购物卡"""

    def test_get_member_list_success(self, member_api, shop_id):
        """正常：获取会员列表"""
        resp = member_api.get_member_list(shop_id)
        data = resp.json()
        assert data["error"] == 0
        assert "members" in data["data"]

    def test_get_member_list_with_keywords(self, member_api, shop_id):
        """正常：带关键词搜索会员"""
        resp = member_api.get_member_list(shop_id, keywords="1020413")
        assert resp.json()["error"] == 0

    def test_get_member_detail_success(self, member_api, shop_id):
        """正常：获取会员详情"""
        member_id = config["member"]["existing_member_id"]
        resp = member_api.get_member_by_id(shop_id, member_id)
        data = resp.json()
        assert data["error"] == 0
        member = data["data"]
        assert member["member_id"] == member_id
        assert "name" in member
        assert "phone" in member

    def test_get_member_detail_not_found(self, member_api, shop_id):
        """异常：查询不存在的会员"""
        resp = member_api.get_member_by_id(shop_id, config["member"]["non_existent_member_id"])
        data = resp.json()
        assert resp.status_code == 200
        assert data["error"] != 0 or data.get("data") is None

    def test_get_member_once_cards(self, member_api, shop_id):
        """正常：会员次卡"""
        member_id = config["member"]["existing_member_id"]
        resp = member_api.get_member_once_cards(
            shop_id, config["shop"]["store_id"], member_id
        )
        assert resp.json()["error"] == 0

    def test_get_member_shopping_cards(self, member_api, shop_id):
        """正常：会员购物卡"""
        member_id = config["member"]["existing_member_id"]
        resp = member_api.get_member_shopping_cards(shop_id, member_id)
        assert resp.json()["error"] == 0


# ╔══════════════════════════════════════════════════════════════╗
# ║                    二、集成接口测试                            ║
# ║    多接口串联验证：加购流程 / 会员切换                          ║
# ╚══════════════════════════════════════════════════════════════╝

@pytest.mark.integration
@pytest.mark.usefixtures("clean_cart")
class TestCashierFlow:
    """【集成】收银台结算流程：加购 → 购物车验证 / 会员切换 → 详情查询"""

    def test_cart_add_and_list(self, cash_api, product_api, shop_id):
        """集成：新建商品 → 入库 → 加购 → 验证购物车列表 → 清理"""
        resp = product_api.add_sku(product_data["product"]["new_sku"])
        product_id = resp.json()["data"]["product_id"]

        try:
            # 入库：新建商品默认库存为0，需先入库才能加购
            resp = product_api.update_stocks(
                shop_id, product_id,
                product_data["product"]["stock_in"]["number"],
                product_data["product"]["stock_in"]["mark"]
            )
            assert resp.json()["error"] == 0, f"入库失败: {resp.json()}"

            cash_api.change_member(shop_id, member_id=-1)

            resp = cash_api.add_to_cart(shop_id, product_id, num=cash_data["cash"]["add_cart"]["num"])
            data = resp.json()
            assert data["error"] == 0, f"加购失败: {data}"
            assert data["data"]["total_num"] >= 1

            resp = cash_api.get_cart_list(shop_id)
            data = resp.json()
            assert data["error"] == 0
            assert data["data"]["total_num"] >= 1
        finally:
            cash_api.change_member(shop_id, member_id=-1)
            product_api.delete_by_ids(shop_id, product_id)

    def test_select_member_and_get_detail(self, cash_api, member_api, shop_id):
        """集成：切换会员 → 查看会员详情 → 查看次卡/购物卡"""
        member_id = config["member"]["existing_member_id"]

        resp = cash_api.change_member(shop_id, member_id=member_id)
        assert resp.json()["error"] == 0

        resp = member_api.get_member_by_id(shop_id, member_id)
        assert resp.json()["error"] == 0
        assert resp.json()["data"]["member_id"] == member_id

        resp = member_api.get_member_once_cards(
            shop_id, config["shop"]["store_id"], member_id
        )
        assert resp.json()["error"] == 0

        resp = member_api.get_member_shopping_cards(shop_id, member_id)
        assert resp.json()["error"] == 0

        # 清理：切换回非会员
        cash_api.change_member(shop_id, member_id=-1)


# ╔══════════════════════════════════════════════════════════════╗
# ║                   三、业务场景测试                             ║
# ║    完整业务链路：端到端验证 + 数据清理                          ║
# ╚══════════════════════════════════════════════════════════════╝

@pytest.mark.scenario
@pytest.mark.usefixtures("clean_cart")
class TestFullOrderScenario:
    """【场景】完整收银下单流程：新建商品→入库→加购→选会员→下单→打印小票→清理"""

    def test_complete_cashier_order_flow(self, product_api, cash_api, member_api, shop_id):
        """
        完整业务场景（11步）：
        新建商品 → 入库 → 重置购物车 → 搜索商品 → 加购 → 切换会员 →
        查看会员详情 → 获取支付方式 → 创建订单 → 打印小票 → 清理
        """
        product_id = None
        order_id = None

        try:
            # Step 1: 新建商品
            resp = product_api.add_sku(product_data["product"]["new_sku"])
            data = resp.json()
            assert data["error"] == 0, f"Step1 新建商品失败: {data}"
            product_id = data["data"]["product_id"]
            logger.info(f"[Step1] 新建商品成功: product_id={product_id}")

            # Step 2: 商品入库
            resp = product_api.update_stocks(
                shop_id, product_id,
                product_data["product"]["stock_in"]["number"],
                product_data["product"]["stock_in"]["mark"]
            )
            assert resp.json()["error"] == 0, f"Step2 入库失败: {resp.json()}"
            logger.info(f"[Step2] 商品入库成功")

            # Step 3: 重置购物车
            resp = cash_api.change_member(shop_id, member_id=-1)
            assert resp.json()["error"] == 0
            logger.info(f"[Step3] 购物车已重置")

            # Step 4: 搜索商品
            resp = cash_api.get_cash_list(shop_id, keywords="自动化测试商品")
            assert resp.json()["error"] == 0
            logger.info(f"[Step4] 搜索商品完成")

            # Step 5: 添加商品到购物车
            resp = cash_api.add_to_cart(shop_id, product_id, num=1)
            data = resp.json()
            assert data["error"] == 0, f"Step5 加购失败: {data}"
            total_price = data["data"]["total_price"]
            logger.info(f"[Step5] 加购成功: total_price={total_price}")

            # Step 6: 切换指定会员
            member_id = config["member"]["existing_member_id"]
            resp = cash_api.change_member(shop_id, member_id=member_id)
            assert resp.json()["error"] == 0
            logger.info(f"[Step6] 已切换会员: member_id={member_id}")

            # Step 7: 查看会员详情/次卡/购物卡
            resp = member_api.get_member_by_id(shop_id, member_id)
            assert resp.json()["error"] == 0
            resp = member_api.get_member_once_cards(
                shop_id, config["shop"]["store_id"], member_id
            )
            assert resp.json()["error"] == 0
            logger.info(f"[Step7] 会员详情查询完成")

            # Step 8: 获取支付方式
            resp = cash_api.get_pay_way_list(shop_id)
            data = resp.json()
            assert data["error"] == 0
            pay_ways = data["data"]["other_pay_way_list"]
            assert len(pay_ways) > 0
            logger.info(f"[Step8] 获取支付方式: {[p['name'] for p in pay_ways]}")

            # Step 9: 创建订单（现金支付）
            resp = cash_api.build_order(
                shop_id,
                pay_ways=[{"way": config["pay_way"]["cash"], "price": total_price}],
                price=total_price
            )
            data = resp.json()
            assert data["error"] == 0, f"Step9 下单失败: {data}"
            order_id = data["data"]["order_id"]
            logger.info(f"[Step9] 下单成功: order_id={order_id}")

            # Step 10: 打印小票
            resp = cash_api.get_print_data(shop_id, order_id)
            data = resp.json()
            assert data["error"] == 0
            assert data["data"]["order_number"] == str(order_id)
            logger.info(f"[Step10] 打印小票成功: {data['data']['store_name']}")

        finally:
            # Step 11: 清理
            cash_api.change_member(shop_id, member_id=-1)
            if product_id:
                resp = product_api.delete_by_ids(shop_id, product_id)
                logger.info(f"[清理] 删除商品 {product_id}: {resp.json().get('message', 'done')}")
            logger.info(f"[完成] 业务场景测试结束, order_id={order_id}")
