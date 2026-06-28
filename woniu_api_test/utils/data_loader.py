"""
YAML 测试数据加载工具
"""
import os
import re
import yaml
from config.settings import TESTDATA_DIR


def _substitute_env_vars(data):
    """递归替换数据中的环境变量占位符 ${VAR_NAME}"""
    if isinstance(data, dict):
        return {k: _substitute_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_substitute_env_vars(item) for item in data]
    elif isinstance(data, str):
        # 匹配 ${VAR_NAME} 格式
        pattern = r'\$\{([^}]+)\}'
        def replace(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))  # 未找到则保留原样
        return re.sub(pattern, replace, data)
    return data


def load_yaml(filename, substitute_env=True):
    """
    加载 testdata 目录下的 YAML 文件，返回 dict。

    Args:
        filename: YAML 文件名
        substitute_env: 是否替换环境变量占位符，默认 True
    """
    filepath = os.path.join(TESTDATA_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"测试数据文件不存在: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if substitute_env:
        data = _substitute_env_vars(data)
    return data
