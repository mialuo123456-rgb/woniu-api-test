# -*- coding: utf-8 -*-
"""
通用工具函数
"""
import time


def generate_unique_phone(prefix: str = "138") -> str:
    """
    生成唯一手机号（基于时间戳）。

    Args:
        prefix: 手机号前缀，默认 "138"

    Returns:
        11 位唯一手机号

    用法:
        phone = generate_unique_phone()        # 138xxxxxxxx
        phone = generate_unique_phone("139")   # 139xxxxxxxx
    """
    return f"{prefix}{int(time.time()) % 100000000:08d}"
