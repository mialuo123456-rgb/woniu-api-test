"""
HTTP 请求客户端封装
基于 requests.Session，自动携带 token + 签名，统一异常处理。
"""
import time
import hashlib
import requests
import logging

from config.settings import BASE_URL, TIMEOUT, DEFAULT_SHOP_ID, DEFAULT_STORE_ID

logger = logging.getLogger(__name__)


class APIClient:
    """封装 HTTP 请求，自动拼接 BASE_URL、携带 token + 计算签名。"""

    def __init__(self, base_url=BASE_URL, token=None, shop=None, store=None, snailuser=None):
        self.base_url = base_url
        self.token = token or ""
        self.shop = str(shop) if shop else "0"
        self.store = str(store) if store else "0"
        self.snailuser = str(snailuser) if snailuser else ""
        self.session = requests.Session()
        # 全局携带客户端版本头信息
        self.session.headers.update({
            "Client-Version": "macOS;null;6.2.0;null",
            "cv": "macOS;",
        })
        if token:
            self.set_token(token)

    def set_token(self, token):
        """设置认证 token（后续所有请求自动携带）。"""
        self.token = token
        self.session.headers.update({"token": token})

    def set_identity(self, shop=None, store=None, snailuser=None):
        """设置店铺/门店/用户身份信息（用于签名计算）。"""
        if shop:
            self.shop = str(shop)
        if store:
            self.store = str(store)
        if snailuser:
            self.snailuser = str(snailuser)

    def _build_url(self, endpoint):
        if endpoint.startswith("http"):
            return endpoint
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    @staticmethod
    def _extract_signable_path(endpoint):
        """提取参与签名的接口路径（去掉域名、query 参数和前导 /）。

        前端签名只用纯路径（如 v2/spu/del），不含 query string。
        """
        # 去掉 query 参数（?xxx=yyy 部分）
        endpoint = endpoint.split("?")[0]
        # 如果是完整 URL，先去掉协议和域名
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            # 取 /api/ 之后的部分
            if "/api/" in endpoint:
                path = endpoint.split("/api/")[1]
            else:
                # 去掉 https://域名/ 前缀
                path = endpoint.split("://", 1)[1]
                path = path.split("/", 1)[1] if "/" in path else path
        else:
            # 相对路径，直接用
            path = endpoint
        return path.lstrip("/")

    def _calc_signature(self, endpoint):
        """计算接口请求签名。

        签名公式: MD5(shop|store|uri|token|Request-Time)
        """
        request_time = str(int(time.time()))
        uri = self._extract_signable_path(endpoint)
        sign_str = f"{self.shop}|{self.store}|{uri}|{self.token}|{request_time}"
        # 清理 "undefined" 字面量
        sign_str = sign_str.replace("undefined", "")
        sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest()
        return sign, request_time

    def request(self, method, endpoint, **kwargs):
        url = self._build_url(endpoint)
        kwargs.setdefault("timeout", TIMEOUT)

        # 每次请求动态计算签名（无论是否有 token 都计算）
        sign, request_time = self._calc_signature(endpoint)
        self.session.headers.update({
            "token": self.token or "",
            "shop": self.shop,
            "store": self.store,
            "snailuser": self.snailuser,
            "Request-Time": request_time,
            "Signature": sign,
        })

        logger.info(f"[{method}] {url}")
        try:
            resp = self.session.request(method, url, **kwargs)
            logger.info(f"[RESP] {resp.status_code} body={resp.text[:300]}")
            return resp
        except requests.Timeout:
            logger.error(f"[TIMEOUT] {method} {url} 请求超时")
            raise
        except requests.ConnectionError as e:
            logger.error(f"[CONN_ERROR] {method} {url} 连接失败: {e}")
            raise
        except requests.RequestException as e:
            logger.error(f"[REQ_ERROR] {method} {url} 请求异常: {e}")
            raise

    def get(self, endpoint, params=None, **kwargs):
        return self.request("GET", endpoint, params=params, **kwargs)

    def post(self, endpoint, json=None, data=None, **kwargs):
        return self.request("POST", endpoint, json=json, data=data, **kwargs)

    def put(self, endpoint, **kwargs):
        return self.request("PUT", endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        return self.request("DELETE", endpoint, **kwargs)
