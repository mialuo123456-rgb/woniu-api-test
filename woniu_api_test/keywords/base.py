# -*- coding: utf-8 -*-
"""
关键字基类 - 所有关键字类的基础
"""
import time
from typing import Any, Dict, List, Optional
from utils.auth_manager import AuthManager
from utils.data_loader import load_yaml
from config.settings import SYNC_WAIT_TIME


class KeywordResult:
    """关键字执行结果封装类。"""

    def __init__(self, success: bool, data: Any = None, message: str = "", response=None):
        self.success = success
        self.data = data
        self.message = message
        self.response = response

    def __bool__(self):
        return self.success

    def __repr__(self):
        status = "成功" if self.success else "失败"
        return f"<KeywordResult [{status}] {self.message}>"


class BaseKeywords:
    """所有关键字实现类的基类。"""

    def __init__(self, client=None):
        self.client = client or AuthManager.get_client()
        self.config = load_yaml("config.yaml")
        self.shop_id = self.config["shop"]["shop_id"]
        self.store_id = self.config["shop"]["store_id"]
        self._context = {}  # 关键字链的共享上下文

    # ========== 上下文管理 ==========

    def set_context(self, key: str, value: Any):
        """存储值到共享上下文。"""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """从共享上下文获取值。"""
        return self._context.get(key, default)

    def clear_context(self):
        """清空所有上下文数据。"""
        self._context.clear()

    # ========== 响应验证关键字 ==========

    def verify_success(self, response, step_name: str = "") -> KeywordResult:
        """
        验证 API 响应是否成功。

        用法:
            result = kw.verify_success(response, "创建会员")
        """
        try:
            data = response.json()
            if data.get("error") == 0:
                return KeywordResult(True, data.get("data"), f"{step_name} 成功")
            else:
                msg = data.get("message", "未知错误")
                return KeywordResult(False, None, f"{step_name} 失败: {msg}", response)
        except Exception as e:
            return KeywordResult(False, None, f"{step_name} 异常: {str(e)}", response)

    def verify_error(self, response, expected_code: int = None, step_name: str = "") -> KeywordResult:
        """
        验证 API 响应是否返回预期的错误。

        用法:
            result = kw.verify_error(response, expected_code=50001, step_name="无效登录")
        """
        try:
            data = response.json()
            error = data.get("error", 0)
            code = data.get("code", 0)

            if error != 0:
                if expected_code is None or code == expected_code:
                    return KeywordResult(True, data, f"{step_name} 错误符合预期")
            return KeywordResult(False, data, f"{step_name} 预期错误但返回成功", response)
        except Exception as e:
            return KeywordResult(False, None, f"{step_name} 异常: {str(e)}", response)

    def verify_data_contains(self, data: Dict, required_fields: List[str], step_name: str = "") -> KeywordResult:
        """
        验证数据是否包含必需字段。

        用法:
            result = kw.verify_data_contains(member, ["member_id", "phone", "name"])
        """
        missing = [f for f in required_fields if f not in data]
        if not missing:
            return KeywordResult(True, data, f"{step_name} 所有字段都存在")
        return KeywordResult(False, data, f"{step_name} 缺少字段: {missing}")

    # ========== 工具方法 ==========

    @staticmethod
    def generate_unique_phone(prefix: str = "138") -> str:
        """
        生成唯一手机号（基于时间戳）。

        用法:
            phone = kw.generate_unique_phone()  # 138xxxxxxxx
            phone = kw.generate_unique_phone("139")  # 139xxxxxxxx
        """
        return f"{prefix}{int(time.time()) % 100000000:08d}"

    # ========== 等待关键字 ==========

    def wait(self, seconds: float = None, reason: str = ""):
        """
        等待指定时间。

        用法:
            kw.wait(2.0, "等待数据同步")
            kw.wait(reason="数据同步")  # 使用默认等待时间
        """
        if seconds is None:
            seconds = SYNC_WAIT_TIME
        time.sleep(seconds)
        return KeywordResult(True, None, f"等待 {seconds} 秒 - {reason}")

    # ========== 清理管理 ==========

    def register_cleanup(self, cleanup_type: str, cleanup_id: Any):
        """注册待清理的资源。"""
        cleanups = self.get_context("_cleanups", [])
        cleanups.append({"type": cleanup_type, "id": cleanup_id})
        self.set_context("_cleanups", cleanups)

    def get_cleanups(self, cleanup_type: str = None) -> List[Dict]:
        """获取已注册的清理项。"""
        cleanups = self.get_context("_cleanups", [])
        if cleanup_type:
            return [c for c in cleanups if c["type"] == cleanup_type]
        return cleanups
