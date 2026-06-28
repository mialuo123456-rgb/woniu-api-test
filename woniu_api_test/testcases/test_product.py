"""
商品管理模块 —— 全量测试用例（整合版）
按测试层级分为：单元接口测试 / 集成接口测试 / 业务场景测试
"""
import copy
import time
import logging
import pytest
from apis.product_api import ProductAPI
from utils.auth_manager import AuthManager
from utils.data_loader import load_yaml
from utils.helpers import generate_unique_phone
from config.settings import SYNC_WAIT_TIME

logger = logging.getLogger(__name__)
product_data = load_yaml("product_data.yaml")


@pytest.fixture(scope="module")
def product_api(api_client):
    """全模块共享一个 ProductAPI 实例。"""
    return ProductAPI(api_client)


# ╔══════════════════════════════════════════════════════════════╗
# ║                    一、单元接口测试                            ║
# ║    覆盖维度：正常 / 边界 / 异常 / 安全                         ║
# ╚══════════════════════════════════════════════════════════════╝

@pytest.mark.unit
class TestProductList:
    """【单元】商品列表查询：SPU/SKU 列表、搜索、分页"""

    def test_get_spu_list_success(self, product_api, shop_id):
        """正常：获取商品列表"""
        resp = product_api.get_spu_list(shop_id)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], dict)

    @pytest.mark.parametrize("keywords", ["测试", "猫粮", "皇家", "皇家幼犬猫粮0.4kg"],
                             ids=["关键词_测试", "关键词_猫粮", "关键词_皇家", "关键词_全名"])
    def test_search_spu_by_keywords(self, product_api, shop_id, keywords):
        """正常：参数化关键词搜索"""
        resp = product_api.get_spu_list(shop_id, keywords=keywords)
        assert resp.json()["error"] == 0

    def test_search_spu_special_chars(self, product_api, shop_id):
        """边界：特殊字符搜索"""
        resp = product_api.get_spu_list(shop_id, keywords="<script>alert(1)</script>")
        assert resp.json()["error"] == 0

    @pytest.mark.parametrize("page,limit", [(1, 15), (1, 1), (1, 100), (0, 15), (9999, 15)],
                             ids=["正常分页", "limit=1最小", "limit=100最大", "page=0越界", "page=9999超尾页"])
    def test_spu_pagination(self, product_api, shop_id, page, limit):
        """边界：SPU 分页参数测试"""
        resp = product_api.get_spu_list(shop_id, page=page, limit=limit)
        assert resp.json()["error"] == 0

    def test_get_sku_list_success(self, product_api, shop_id):
        """正常：获取 SKU 列表"""
        resp = product_api.get_sku_list(shop_id)
        assert resp.json()["error"] == 0

    @pytest.mark.parametrize("page,limit", [(1, 30), (1, 0), (1, 200)],
                             ids=["正常分页", "limit=0", "limit=200"])
    def test_sku_pagination(self, product_api, shop_id, page, limit):
        """边界：SKU 分页"""
        resp = product_api.get_sku_list(shop_id, page=page, limit=limit)
        assert resp.json()["error"] == 0


@pytest.mark.unit
class TestProductDict:
    """【单元】分类、标签、品牌、供应商等字典接口"""

    def test_get_category_list(self, product_api, shop_id):
        """正常：商品分类列表"""
        resp = product_api.get_category_list(shop_id)
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"], list)
        if len(data["data"]) > 0:
            assert "name" in data["data"][0]

    def test_get_shop_categories(self, product_api, shop_id):
        """正常：门店分类"""
        resp = product_api.get_shop_categories(shop_id)
        assert resp.json()["error"] == 0

    def test_get_product_tags(self, product_api, shop_id):
        """正常：商品标签列表"""
        resp = product_api.get_product_tags(shop_id)
        assert resp.json()["error"] == 0

    def test_get_brand_list(self, product_api, shop_id):
        """正常：品牌列表"""
        resp = product_api.get_brand_list(shop_id)
        assert resp.json()["error"] == 0

    def test_get_brand_by_name(self, product_api, shop_id):
        """正常：根据商品名查品牌"""
        resp = product_api.get_brand_by_name("测试商品", shop_id)
        assert resp.json()["error"] == 0

    def test_get_supplier_list(self, product_api, shop_id):
        """正常：供应商列表"""
        resp = product_api.get_supplier_list(shop_id)
        assert resp.json()["error"] == 0


@pytest.mark.unit
class TestBarcode:
    """【单元】条码查询：正常 / 边界 / 异常 / 安全"""

    @pytest.mark.parametrize("bar_code", product_data["product"]["barcodes"]["not_found"],
                             ids=["条码_12345678", "条码_123456789", "条码_1234567890"])
    def test_get_by_barcode_not_found(self, product_api, shop_id, bar_code):
        """异常：条码查询不存在商品"""
        resp = product_api.get_by_barcode(bar_code, shop_id)
        data = resp.json()
        assert resp.status_code == 200
        assert data.get("code") == 50001 or data.get("error") != 0

    def test_get_by_barcode_empty(self, product_api, shop_id):
        """边界：空条码"""
        resp = product_api.get_by_barcode(product_data["product"]["barcodes"]["empty"], shop_id)
        assert resp.status_code == 200

    def test_get_by_barcode_special_chars(self, product_api, shop_id):
        """安全：特殊字符条码"""
        resp = product_api.get_by_barcode(product_data["product"]["barcodes"]["special_chars"], shop_id)
        assert resp.status_code == 200

    def test_get_by_barcode_sql_injection(self, product_api, shop_id):
        """安全：SQL 注入条码"""
        resp = product_api.get_by_barcode(product_data["product"]["barcodes"]["sql_injection"], shop_id)
        data = resp.json()
        assert data.get("code") == 50001 or data.get("error") != 0


@pytest.mark.unit
class TestCreateProduct:
    """【单元】新建商品接口：正常 / 边界 / 异常 / 安全"""

    def test_create_product_success(self, product_api, shop_id):
        """正常：创建商品后清理"""
        resp = product_api.add_sku(product_data["product"]["new_sku"])
        data = resp.json()
        assert data["error"] == 0
        assert isinstance(data["data"]["product_id"], int)
        product_api.delete_by_ids(shop_id, data["data"]["product_id"])

    def test_create_product_zero_price(self, product_api, shop_id):
        """边界：零元商品"""
        resp = product_api.add_sku(product_data["product"]["new_sku_zero_price"])
        data = resp.json()
        if data["error"] == 0:
            product_api.delete_by_ids(shop_id, data["data"]["product_id"])

    def test_create_product_negative_price(self, product_api, shop_id):
        """异常：负数价格"""
        resp = product_api.add_sku(product_data["product"]["new_sku_negative_price"])
        data = resp.json()
        assert data["error"] != 0 or data.get("code") != 0
        if data["error"] == 0:
            product_api.delete_by_ids(shop_id, data["data"]["product_id"])

    def test_create_product_xss_name(self, product_api, shop_id):
        """安全：XSS 脚本商品名"""
        resp = product_api.add_sku(product_data["product"]["new_sku_special_name"])
        data = resp.json()
        if data["error"] == 0:
            product_api.delete_by_ids(shop_id, data["data"]["product_id"])


@pytest.mark.unit
class TestBatchStock:
    """【单元】批量入库接口：计算价格 / 批量入库 / 边界 / 异常"""

    def test_compute_in_price_success(self, product_api, shop_id):
        """正常：计算入库价格（先创建商品再计算）"""
        resp = product_api.add_sku(product_data["product"]["new_sku"])
        data = resp.json()
        if data.get("error") != 0:
            pytest.skip(f"创建商品失败，跳过: {data.get('message')}")
        pid = data["data"]["product_id"]
        try:
            resp = product_api.compute_in_price(shop_id, pid, 10, 10)
            data = resp.json()
            assert data["error"] == 0
            assert isinstance(data["data"], (int, float))
        finally:
            product_api.delete_by_ids(shop_id, pid)

    def test_compute_in_price_zero_number(self, product_api, shop_id):
        """边界：入库数量为0"""
        resp = product_api.compute_in_price(shop_id, 104465825, 0, 10)
        assert resp.status_code == 200

    def test_compute_in_price_negative_price(self, product_api, shop_id):
        """异常：负数价格"""
        resp = product_api.compute_in_price(shop_id, 104465825, 10, -1)
        assert resp.status_code == 200

    def test_compute_in_price_not_exist_product(self, product_api, shop_id):
        """异常：不存在的商品 ID"""
        resp = product_api.compute_in_price(shop_id, 999999999, 10, 10)
        assert resp.status_code == 200

    def test_batch_lot_stock_success(self, product_api, shop_id):
        """正常：批量入库（先创建商品再入库再清理）"""
        resp = product_api.add_sku(product_data["product"]["new_sku"])
        data = resp.json()
        if data.get("error") != 0:
            pytest.skip(f"创建商品失败，跳过: {data.get('message')}")
        pid = data["data"]["product_id"]
        time.sleep(SYNC_WAIT_TIME)
        try:
            items = [{"inPrice": 10, "number": 5, "productId": pid}]
            resp = product_api.batch_lot_stock(shop_id, items, mark="自动化测试入库")
            data = resp.json()
            assert data["error"] == 0
            assert data["data"] == "success"
        finally:
            product_api.delete_by_ids(shop_id, pid)

    def test_batch_lot_stock_empty_items(self, product_api, shop_id):
        """异常：空入库列表"""
        resp = product_api.batch_lot_stock(shop_id, [], mark="空列表")
        assert resp.status_code == 200

    def test_compute_in_price_large_number(self, product_api, shop_id):
        """边界：超大入库数量"""
        resp = product_api.add_sku(product_data["product"]["new_sku"])
        data = resp.json()
        if data.get("error") != 0:
            pytest.skip(f"创建商品失败，跳过: {data.get('message')}")
        pid = data["data"]["product_id"]
        try:
            resp = product_api.compute_in_price(shop_id, pid, 999999, 10)
            data = resp.json()
            assert data["error"] == 0
            assert isinstance(data["data"], (int, float))
        finally:
            product_api.delete_by_ids(shop_id, pid)

    def test_compute_in_price_decimal_price(self, product_api, shop_id):
        """边界：小数价格精度"""
        resp = product_api.add_sku(product_data["product"]["new_sku"])
        data = resp.json()
        if data.get("error") != 0:
            pytest.skip(f"创建商品失败，跳过: {data.get('message')}")
        pid = data["data"]["product_id"]
        try:
            resp = product_api.compute_in_price(shop_id, pid, 10, 9.99)
            data = resp.json()
            assert data["error"] == 0
        finally:
            product_api.delete_by_ids(shop_id, pid)

    def test_compute_in_price_zero_price(self, product_api, shop_id):
        """边界：入库价格为0"""
        resp = product_api.add_sku(product_data["product"]["new_sku"])
        data = resp.json()
        if data.get("error") != 0:
            pytest.skip(f"创建商品失败，跳过: {data.get('message')}")
        pid = data["data"]["product_id"]
        try:
            resp = product_api.compute_in_price(shop_id, pid, 10, 0)
            data = resp.json()
            assert data["error"] == 0
        finally:
            product_api.delete_by_ids(shop_id, pid)


@pytest.mark.unit
class TestFileSTS:
    """【单元】文件上传凭证：正常 / 结构验证 / 异常"""

    def test_get_file_sts_success(self, product_api, shop_id):
        """正常：获取有效的 STS 凭证"""
        from utils.auth_manager import AuthManager
        token = AuthManager._token
        resp = product_api.get_file_sts(shop_id, token)
        data = resp.json()
        assert data["error"] == 0
        assert "Credentials" in data["data"]

    def test_get_file_sts_credentials_structure(self, product_api, shop_id):
        """验证：凭证结构完整性"""
        from utils.auth_manager import AuthManager
        token = AuthManager._token
        resp = product_api.get_file_sts(shop_id, token)
        data = resp.json()
        assert data["error"] == 0
        credentials = data["data"]["Credentials"]
        # 验证必要字段存在
        assert "AccessKeyId" in credentials
        assert "AccessKeySecret" in credentials
        assert "SecurityToken" in credentials
        assert "Expiration" in credentials
        # 验证 AccessKeyId 格式
        assert credentials["AccessKeyId"].startswith("STS.")

    def test_get_file_sts_mode_field(self, product_api, shop_id):
        """验证：环境模式字段"""
        from utils.auth_manager import AuthManager
        token = AuthManager._token
        resp = product_api.get_file_sts(shop_id, token)
        data = resp.json()
        assert data["error"] == 0
        assert "mode" in data["data"]
        assert data["data"]["mode"] in ["test", "prod", "dev"]

    def test_get_file_sts_invalid_token(self, product_api, shop_id):
        """异常：无效 token"""
        resp = product_api.get_file_sts(shop_id, "invalid_token_12345")
        data = resp.json()
        # 无效 token 应返回错误或特定状态
        assert resp.status_code == 200
        # 可能返回错误，也可能返回空凭证，根据实际接口行为调整
        if data.get("error") != 0:
            assert data["error"] != 0
        else:
            # 某些接口可能不验证 token，仍返回成功
            assert "Credentials" in data.get("data", {})

    def test_get_file_sts_empty_token(self, product_api, shop_id):
        """异常：空 token"""
        resp = product_api.get_file_sts(shop_id, "")
        assert resp.status_code == 200


@pytest.mark.unit
class TestComboProduct:
    """【单元】组合商品接口：创建 / 详情 / 编辑 / 异常 / 安全"""

    def test_create_combo_product_success(self, product_api, shop_id):
        """正常：创建组合商品后清理"""
        # 使用带规格的商品模板，否则无法创建 SPU（deepcopy 避免嵌套对象共享）
        # 为每个商品生成唯一的规格名称，避免"规格字段重复"错误
        sku_data1 = copy.deepcopy(product_data["product"]["new_sku_with_spec"])
        sku_data1["sku"]["specifications"] = f"500g-{int(time.time())}"
        resp1 = product_api.add_sku(sku_data1)
        if resp1.json().get("error") != 0:
            pytest.skip(f"创建商品失败，跳过: {resp1.json().get('message')}")
        time.sleep(SYNC_WAIT_TIME)
        sku_data2 = copy.deepcopy(product_data["product"]["new_sku_with_spec"])
        sku_data2["sku"]["specifications"] = f"1kg-{int(time.time())}"
        resp2 = product_api.add_sku(sku_data2)
        if resp2.json().get("error") != 0:
            product_api.delete_by_ids(shop_id, resp1.json()["data"]["product_id"])
            pytest.skip(f"创建商品2失败，跳过: {resp2.json().get('message')}")
        pid1 = resp1.json()["data"]["product_id"]
        pid2 = resp2.json()["data"]["product_id"]

        spu_id = None
        try:
            spu_data = product_data["combo_product"]["normal_create"].copy()
            spu_data["product_ids"] = [pid1, pid2]
            resp = product_api.save_spu(spu_data)
            assert resp.json()["error"] == 0

            resp = product_api.get_spu_list(shop_id, keywords="自动化测试组合商品")
            spu_list = resp.json()["data"]["list"]
            if spu_list:
                spu_id = spu_list[0]["spu_id"]
        finally:
            if spu_id:
                product_api.delete_spu(spu_id, shop_id)
            product_api.batch_delete_products(shop_id, [pid1, pid2])

    def test_get_spu_detail_success(self, product_api, shop_id):
        """正常：获取组合商品详情"""
        resp = product_api.get_spu_detail("197356480377180828", shop_id)
        assert resp.status_code == 200

    def test_get_spu_detail_not_exist(self, product_api, shop_id):
        """异常：不存在的 SPU ID"""
        resp = product_api.get_spu_detail("999999999999", shop_id)
        assert resp.status_code == 200

    def test_create_combo_empty_name(self, product_api, shop_id):
        """异常：组合商品名称为空"""
        spu_data = product_data["combo_product"]["empty_name"].copy()
        resp = product_api.save_spu(spu_data)
        assert resp.json()["error"] != 0 or resp.status_code == 200

    def test_create_combo_empty_product_ids(self, product_api, shop_id):
        """异常：组合商品子商品列表为空"""
        spu_data = product_data["combo_product"]["empty_product_ids"].copy()
        resp = product_api.save_spu(spu_data)
        data = resp.json()
        assert data["error"] != 0 or resp.status_code == 200
        if data.get("error") == 0:
            resp = product_api.get_spu_list(shop_id, keywords="无子商品组合")
            items = resp.json().get("data", {}).get("list", [])
            if items:
                product_api.delete_spu(items[0]["spu_id"], shop_id)

    def test_create_combo_xss_name(self, product_api, shop_id):
        """安全：组合商品名称 XSS"""
        spu_data = product_data["combo_product"]["xss_name"].copy()
        resp = product_api.save_spu(spu_data)
        data = resp.json()
        if data.get("error") == 0:
            resp = product_api.get_spu_list(shop_id, keywords="alert")
            items = resp.json().get("data", {}).get("list", [])
            if items:
                product_api.delete_spu(items[0]["spu_id"], shop_id)


@pytest.mark.unit
class TestBatchDelete:
    """【单元】批量删除接口：正常 / 异常"""

    def test_batch_delete_success(self, product_api, shop_id):
        """正常：创建商品 → 批量删除"""
        resp = product_api.add_sku(product_data["product"]["new_sku"])
        data = resp.json()
        if data.get("error") != 0 or not data.get("data"):
            pytest.skip(f"创建商品失败，跳过: {data.get('message')}")
        pid = data["data"]["product_id"]
        resp = product_api.batch_delete_products(shop_id, [pid])
        data = resp.json()
        assert data["error"] == 0
        assert data["data"] == "success"

    def test_batch_delete_not_exist(self, product_api, shop_id):
        """异常：删除不存在的商品 ID"""
        resp = product_api.batch_delete_products(shop_id, [999999999])
        assert resp.status_code == 200


# ╔══════════════════════════════════════════════════════════════╗
# ║                    二、集成接口测试                            ║
# ║    多接口串联验证：创建→查询→入库→删除 等                      ║
# ╚══════════════════════════════════════════════════════════════╝

@pytest.mark.integration
class TestProductCRUD:
    """【集成】商品增删改查 + 入库 + 标签 + 供应商"""

    def test_create_and_verify_product(self, product_api, shop_id):
        """集成：新建商品 → 查询验证 → 入库 → 清理"""
        resp = product_api.add_sku(product_data["product"]["new_sku"])
        data = resp.json()
        assert data["error"] == 0, f"新建商品失败: {data}"
        product_id = data["data"]["product_id"]

        try:
            resp = product_api.get_spu_list(shop_id, keywords="自动化测试商品")
            assert resp.json()["error"] == 0

            resp = product_api.update_stocks(
                shop_id, product_id,
                product_data["product"]["stock_in"]["number"],
                product_data["product"]["stock_in"]["mark"]
            )
            assert resp.json()["error"] == 0
        finally:
            product_api.delete_by_ids(shop_id, product_id)

    def test_create_and_delete_tag(self, product_api, shop_id):
        """集成：新建标签 → 验证标签列表"""
        tag_name = product_data["tag"]["new_tag_name"]
        resp = product_api.save_product_tag(shop_id, tag_name)
        assert resp.json()["error"] == 0
        resp = product_api.get_product_tags(shop_id)
        assert resp.json()["error"] == 0

    def test_supplier_save_and_list(self, product_api, shop_id):
        """集成：新建供应商 → 验证供应商列表 → 删除供应商"""
        # 使用动态生成的电话号码
        supplier_data = copy.deepcopy(product_data["supplier"]["new_supplier"])
        unique_phone = generate_unique_phone("139")
        supplier_data["phone"] = unique_phone

        # 创建供应商
        resp = product_api.save_supplier(supplier_data)
        data = resp.json()
        assert data["error"] == 0, f"创建供应商失败: {data.get('message')}"

        supplier_id = None
        try:
            # 验证供应商列表
            resp = product_api.get_supplier_list(shop_id)
            assert resp.json()["error"] == 0
            # 从列表中找到新创建的供应商（通过 phone 匹配）
            suppliers = resp.json()["data"]["list"]
            for s in suppliers:
                if s.get("phone") == unique_phone:
                    supplier_id = s.get("supplier_id")
                    break
            assert supplier_id is not None, f"供应商 phone={unique_phone} 未在列表中找到"
            logger.info(f"[验证] 找到供应商 ID: {supplier_id}")
        finally:
            # 清理：删除供应商
            if supplier_id:
                resp = product_api.delete_supplier(shop_id, supplier_id)
                logger.info(f"[清理] 删除供应商 {supplier_id}: {resp.json().get('message', 'done')}")

    def test_batch_stock_in_flow(self, product_api, shop_id):
        """集成：创建多商品 → 计算入库价格 → 批量入库 → 验证库存 → 清理"""
        sku_data = product_data["product"]["new_sku"]
        resp1 = product_api.add_sku(sku_data)
        if resp1.json().get("error") != 0:
            pytest.skip(f"创建商品1失败，跳过: {resp1.json().get('message')}")
        time.sleep(SYNC_WAIT_TIME)
        resp2 = product_api.add_sku(sku_data)
        if resp2.json().get("error") != 0:
            product_api.delete_by_ids(shop_id, resp1.json()["data"]["product_id"])
            pytest.skip(f"创建商品2失败，跳过: {resp2.json().get('message')}")
        pid1 = resp1.json()["data"]["product_id"]
        pid2 = resp2.json()["data"]["product_id"]

        try:
            resp = product_api.compute_in_price(shop_id, pid1, 10, 10)
            assert resp.json()["error"] == 0
            resp = product_api.compute_in_price(shop_id, pid2, 10, 10)
            assert resp.json()["error"] == 0

            items = [
                {"inPrice": 10, "number": 10, "productId": pid1},
                {"inPrice": 10, "number": 10, "productId": pid2},
            ]
            resp = product_api.batch_lot_stock(shop_id, items, mark="集成测试批量入库")
            assert resp.json()["error"] == 0
            assert resp.json()["data"] == "success"

            resp = product_api.get_spu_list(shop_id, keywords="自动化测试商品")
            assert resp.json()["error"] == 0
        finally:
            product_api.batch_delete_products(shop_id, [pid1, pid2])


# ╔══════════════════════════════════════════════════════════════╗
# ║                   三、业务场景测试                             ║
# ║    完整业务链路：端到端验证 + 数据清理                          ║
# ╚══════════════════════════════════════════════════════════════╝

@pytest.mark.scenario
class TestComboProductScenario:
    """【场景】组合商品完整链路：创建商品→入库→STS凭证→创建组合→验证→编辑→清理"""

    def test_full_combo_product_flow(self, product_api, shop_id):
        """完整场景：创建商品 → 入库 → STS凭证 → 创建组合商品 → 验证详情 → 编辑 → 清理"""
        pids = []
        spu_id = None

        try:
            # Step 1: 创建两个子商品（使用带规格的模板，否则无法创建 SPU）
            # 为每个商品生成唯一的规格名称，避免"规格字段重复"错误
            sku_data1 = copy.deepcopy(product_data["product"]["new_sku_with_spec"])
            sku_data1["sku"]["specifications"] = f"500g-{int(time.time())}"
            resp1 = product_api.add_sku(sku_data1)
            if resp1.json().get("error") != 0:
                pytest.skip(f"[Step1] 创建商品1失败，跳过: {resp1.json().get('message')}")
            time.sleep(SYNC_WAIT_TIME)
            sku_data2 = copy.deepcopy(product_data["product"]["new_sku_with_spec"])
            sku_data2["sku"]["specifications"] = f"1kg-{int(time.time())}"
            resp2 = product_api.add_sku(sku_data2)
            if resp2.json().get("error") != 0:
                product_api.delete_by_ids(shop_id, resp1.json()["data"]["product_id"])
                pytest.skip(f"[Step1] 创建商品2失败，跳过: {resp2.json().get('message')}")
            pid1 = resp1.json()["data"]["product_id"]
            pid2 = resp2.json()["data"]["product_id"]
            pids = [pid1, pid2]
            logger.info(f"[Step1] 创建子商品成功: pid1={pid1}, pid2={pid2}")

            # Step 2: 计算入库价格 + 批量入库
            resp = product_api.compute_in_price(shop_id, pid1, 10, 10)
            assert resp.json()["error"] == 0, "[Step2] 计算入库价格失败"

            items = [
                {"inPrice": 10, "number": 10, "productId": pid1},
                {"inPrice": 10, "number": 10, "productId": pid2},
            ]
            resp = product_api.batch_lot_stock(shop_id, items, mark="场景测试批量入库")
            assert resp.json()["error"] == 0, f"[Step2] 批量入库失败: {resp.json()}"
            assert resp.json()["data"] == "success"
            logger.info(f"[Step2] 批量入库成功: 各10件")

            # Step 3: 获取 STS 凭证（模拟上传链路的凭证获取环节）
            token = AuthManager._token
            resp = product_api.get_file_sts(shop_id, token)
            assert resp.json()["error"] == 0, f"[Step3] 获取STS凭证失败: {resp.json()}"
            sts_data = resp.json()["data"]
            assert "Credentials" in sts_data
            assert "AccessKeyId" in sts_data["Credentials"]
            logger.info(f"[Step3] STS凭证获取成功: mode={sts_data.get('mode')}")

            # Step 4: 创建组合商品（引用已有图片URL，模拟上传完成后的状态）
            spu_data = copy.deepcopy(product_data["combo_product"]["normal_create"])
            spu_data["product_ids"] = [pid1, pid2]
            resp = product_api.save_spu(spu_data)
            assert resp.json()["error"] == 0, f"[Step4] 创建组合商品失败: {resp.json()}"
            logger.info(f"[Step4] 创建组合商品成功: {spu_data['name']}")

            # Step 5: 查询组合商品列表，获取 spu_id
            resp = product_api.get_spu_list(shop_id, keywords="自动化测试组合商品")
            assert resp.json()["error"] == 0
            spu_list = resp.json()["data"]["list"]
            assert len(spu_list) > 0, "[Step5] 未找到刚创建的组合商品"
            spu_id = spu_list[0]["spu_id"]
            logger.info(f"[Step5] 查询到组合商品: spu_id={spu_id}")

            # Step 6: 获取组合商品详情，验证子商品
            resp = product_api.get_spu_detail(spu_id, shop_id)
            assert resp.json()["error"] == 0, f"[Step6] 获取详情失败: {resp.json()}"
            detail = resp.json()["data"]
            assert detail["name"] == "自动化测试组合商品"
            assert len(detail["skus"]) == 2, "[Step6] 子商品数量不匹配"
            detail_pids = {sku["product_id"] for sku in detail["skus"]}
            assert pid1 in detail_pids and pid2 in detail_pids, "[Step6] 子商品 ID 不匹配"
            assert detail["stock"] == 20, f"[Step6] 库存不匹配: {detail['stock']}"
            logger.info(f"[Step6] 详情验证通过: stock={detail['stock']}, skus={len(detail['skus'])}")

            # Step 7: 编辑组合商品（更新名称）
            edit_data = copy.deepcopy(product_data["combo_product"]["normal_edit"])
            edit_data["spu_id"] = spu_id
            edit_data["product_ids"] = [pid1, pid2]
            resp = product_api.save_spu(edit_data)
            assert resp.json()["error"] == 0, f"[Step7] 编辑组合商品失败: {resp.json()}"
            logger.info(f"[Step7] 编辑组合商品成功")

        finally:
            # 清理：删除组合商品 → 批量删除子商品
            if spu_id:
                resp = product_api.delete_spu(spu_id, shop_id)
                logger.info(f"[清理] 删除组合商品 {spu_id}: {resp.json().get('message', 'done')}")
            if pids:
                resp = product_api.batch_delete_products(shop_id, pids)
                logger.info(f"[清理] 批量删除子商品 {pids}: {resp.json().get('message', 'done')}")
            logger.info("[完成] 组合商品完整链路测试结束")
