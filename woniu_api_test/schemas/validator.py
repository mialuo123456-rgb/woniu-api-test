"""
JSON Schema 校验工具
"""
import jsonschema
from jsonschema import validate, ValidationError


def validate_response(response_data: dict, schema: dict) -> tuple[bool, str]:
    """
    校验响应数据是否符合 Schema

    :param response_data: 接口响应的 JSON 数据
    :param schema: JSON Schema 定义
    :return: (是否通过, 错误信息)
    """
    try:
        validate(instance=response_data, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, f"Schema 校验失败: {e.message} (path: {list(e.path)})"


def assert_schema(response_data: dict, schema: dict, msg: str = ""):
    """
    断言响应数据符合 Schema，失败时抛出 AssertionError

    :param response_data: 接口响应的 JSON 数据
    :param schema: JSON Schema 定义
    :param msg: 自定义错误消息前缀
    """
    is_valid, error = validate_response(response_data, schema)
    if not is_valid:
        prefix = f"{msg}: " if msg else ""
        raise AssertionError(f"{prefix}{error}")


class SchemaValidator:
    """Schema 校验器类，支持链式调用"""

    def __init__(self, response):
        """
        :param response: requests.Response 对象或 dict
        """
        if hasattr(response, 'json'):
            self.data = response.json()
        else:
            self.data = response
        self.errors = []

    def validate(self, schema: dict) -> 'SchemaValidator':
        """校验 Schema"""
        is_valid, error = validate_response(self.data, schema)
        if not is_valid:
            self.errors.append(error)
        return self

    def has_field(self, *fields) -> 'SchemaValidator':
        """校验字段存在"""
        for field in fields:
            if field not in self.data:
                self.errors.append(f"缺少字段: {field}")
        return self

    def field_type(self, field: str, expected_type: type) -> 'SchemaValidator':
        """校验字段类型"""
        if field in self.data:
            if not isinstance(self.data[field], expected_type):
                self.errors.append(
                    f"字段 {field} 类型错误: 期望 {expected_type.__name__}, "
                    f"实际 {type(self.data[field]).__name__}"
                )
        return self

    def is_success(self) -> 'SchemaValidator':
        """校验接口返回成功（error=0）"""
        if self.data.get("error") != 0:
            self.errors.append(f"接口返回错误: error={self.data.get('error')}, "
                             f"message={self.data.get('message')}")
        return self

    def assert_valid(self, msg: str = ""):
        """断言所有校验通过"""
        if self.errors:
            prefix = f"{msg}: " if msg else ""
            raise AssertionError(f"{prefix}" + "; ".join(self.errors))
        return self

    def get_data(self, key: str = "data"):
        """获取响应中的数据"""
        return self.data.get(key)
