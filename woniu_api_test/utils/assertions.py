"""
统一断言封装
提供常用的接口响应断言方法
"""
import json
from typing import Any, List, Optional


class APIAssertions:
    """API 响应断言工具类"""

    @staticmethod
    def assert_success(response, msg: str = "") -> dict:
        """
        断言接口返回成功（error=0）

        :param response: requests.Response 对象
        :param msg: 自定义错误消息
        :return: 响应的 JSON 数据
        """
        data = response.json()
        prefix = f"{msg}: " if msg else ""
        assert data.get("error") == 0, (
            f"{prefix}接口返回错误: error={data.get('error')}, "
            f"message={data.get('message')}"
        )
        return data

    @staticmethod
    def assert_error(response, expected_code: int = None, msg: str = "") -> dict:
        """
        断言接口返回错误

        :param response: requests.Response 对象
        :param expected_code: 期望的错误码（可选）
        :param msg: 自定义错误消息
        :return: 响应的 JSON 数据
        """
        data = response.json()
        prefix = f"{msg}: " if msg else ""
        assert data.get("error") != 0, f"{prefix}期望接口返回错误，但实际成功"
        if expected_code is not None:
            assert data.get("code") == expected_code, (
                f"{prefix}错误码不匹配: 期望 {expected_code}, 实际 {data.get('code')}"
            )
        return data

    @staticmethod
    def assert_status_code(response, expected: int = 200, msg: str = ""):
        """断言 HTTP 状态码"""
        prefix = f"{msg}: " if msg else ""
        assert response.status_code == expected, (
            f"{prefix}HTTP 状态码错误: 期望 {expected}, 实际 {response.status_code}"
        )

    @staticmethod
    def assert_has_fields(data: dict, *fields, msg: str = ""):
        """
        断言响应数据包含指定字段

        :param data: 响应数据字典
        :param fields: 必须存在的字段名
        :param msg: 自定义错误消息
        """
        prefix = f"{msg}: " if msg else ""
        missing = [f for f in fields if f not in data]
        assert not missing, f"{prefix}缺少必要字段: {missing}"

    @staticmethod
    def assert_field_type(data: dict, field: str, expected_type: type, msg: str = ""):
        """
        断言字段类型

        :param data: 响应数据字典
        :param field: 字段名
        :param expected_type: 期望的类型
        :param msg: 自定义错误消息
        """
        prefix = f"{msg}: " if msg else ""
        assert field in data, f"{prefix}字段 {field} 不存在"
        actual_type = type(data[field])
        assert isinstance(data[field], expected_type), (
            f"{prefix}字段 {field} 类型错误: 期望 {expected_type.__name__}, "
            f"实际 {actual_type.__name__}"
        )

    @staticmethod
    def assert_field_value(data: dict, field: str, expected_value: Any, msg: str = ""):
        """
        断言字段值

        :param data: 响应数据字典
        :param field: 字段名
        :param expected_value: 期望的值
        :param msg: 自定义错误消息
        """
        prefix = f"{msg}: " if msg else ""
        assert field in data, f"{prefix}字段 {field} 不存在"
        assert data[field] == expected_value, (
            f"{prefix}字段 {field} 值错误: 期望 {expected_value}, 实际 {data[field]}"
        )

    @staticmethod
    def assert_list_not_empty(data: dict, list_field: str = "list", msg: str = ""):
        """
        断言列表字段不为空

        :param data: 响应数据字典
        :param list_field: 列表字段名
        :param msg: 自定义错误消息
        """
        prefix = f"{msg}: " if msg else ""
        target = data.get("data", data)
        items = target.get(list_field, [])
        assert items and len(items) > 0, f"{prefix}列表 {list_field} 为空"

    @staticmethod
    def assert_pagination(data: dict, page: int = 1, limit: int = 15, msg: str = ""):
        """
        断言分页信息正确

        :param data: 响应数据字典
        :param page: 期望的当前页
        :param limit: 期望的每页数量
        :param msg: 自定义错误消息
        """
        prefix = f"{msg}: " if msg else ""
        pager = data.get("data", {}).get("pager", {})
        assert pager.get("currentPage") == page, (
            f"{prefix}当前页错误: 期望 {page}, 实际 {pager.get('currentPage')}"
        )
        assert pager.get("limit") == limit, (
            f"{prefix}每页数量错误: 期望 {limit}, 实际 {pager.get('limit')}"
        )

    @staticmethod
    def assert_in_range(value: Any, min_val: Any, max_val: Any, msg: str = ""):
        """
        断言值在指定范围内

        :param value: 要检查的值
        :param min_val: 最小值
        :param max_val: 最大值
        :param msg: 自定义错误消息
        """
        prefix = f"{msg}: " if msg else ""
        assert min_val <= value <= max_val, (
            f"{prefix}值 {value} 不在范围 [{min_val}, {max_val}] 内"
        )

    @staticmethod
    def assert_contains(text: str, substring: str, msg: str = ""):
        """断言字符串包含子串"""
        prefix = f"{msg}: " if msg else ""
        assert substring in text, f"{prefix}'{text}' 不包含 '{substring}'"

    @staticmethod
    def assert_not_contains(text: str, substring: str, msg: str = ""):
        """断言字符串不包含子串（用于 XSS 检测）"""
        prefix = f"{msg}: " if msg else ""
        assert substring not in text, f"{prefix}'{text}' 不应包含 '{substring}'"


# 便捷函数
def assert_api_success(response, msg: str = "") -> dict:
    """断言接口成功的便捷函数"""
    return APIAssertions.assert_success(response, msg)


def assert_api_error(response, expected_code: int = None, msg: str = "") -> dict:
    """断言接口错误的便捷函数"""
    return APIAssertions.assert_error(response, expected_code, msg)
