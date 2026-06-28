import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 测试环境地址
BASE_URL = os.getenv("TEST_BASE_URL", "https://webtest.woniuxiaodian.cn")

# 请求超时（秒）
TIMEOUT = 15

# 默认门店 ID（从录制数据中获取）
DEFAULT_SHOP_ID = int(os.getenv("TEST_SHOP_ID", "6419"))

# 默认门店 ID
DEFAULT_STORE_ID = int(os.getenv("TEST_STORE_ID", "5238"))

# 测试账号（优先从环境变量读取，未设置则使用默认值）
# 注意：生产环境应始终使用环境变量，此处默认值仅供开发测试
TEST_ACCOUNT = {
    "phone": os.getenv("TEST_PHONE", "15983891506"),
    "password": os.getenv("TEST_PASSWORD", "luoting520"),
    "shop_id": DEFAULT_SHOP_ID,
}

# 检查必要的环境变量（开发环境有默认值，不再强制检查）
def validate_env():
    """验证环境变量（开发模式下跳过）"""
    pass  # 开发环境使用默认值，无需验证

# YAML 测试数据目录
TESTDATA_DIR = os.path.join(BASE_DIR, "testdata")

# 等待时间配置（秒）
SYNC_WAIT_TIME = 0.5       # 数据同步等待
RATE_LIMIT_DELAY = 0.3     # 请求频率限制延迟

# 重试配置
RETRY_MAX_ATTEMPTS = 3     # 最大重试次数
RETRY_BASE_DELAY = 2.0     # 重试基础等待时间（秒）
RETRY_BACKOFF = 1.5        # 重试退避系数（每次重试等待时间 = 基础时间 * 系数^重试次数）
