"""
商品模块 JSON Schema 定义
用于校验接口响应结构的完整性
"""

# 通用响应结构
BASE_RESPONSE = {
    "type": "object",
    "required": ["error"],
    "properties": {
        "error": {"type": "integer"},
        "code": {"type": "integer"},
        "biz_code": {"type": "integer"},
        "message": {"type": "string"},
        "success": {"type": "boolean"},
        "trace_id": {"type": "string"},
        "req_id": {"type": "string"},
    }
}

# 新建商品响应
ADD_SKU_RESPONSE = {
    "type": "object",
    "required": ["error", "data"],
    "properties": {
        "error": {"type": "integer", "enum": [0]},
        "data": {
            "type": "object",
            "required": ["product_id"],
            "properties": {
                "product_id": {"type": "integer"},
                "spu_id": {"type": "string"}
            }
        }
    }
}

# 商品列表响应
SPU_LIST_RESPONSE = {
    "type": "object",
    "required": ["error", "data"],
    "properties": {
        "error": {"type": "integer", "enum": [0]},
        "data": {
            "type": "object",
            "required": ["list", "pager"],
            "properties": {
                "list": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "product_id": {"type": "integer"},
                            "barcode": {"type": "string"},
                            "out_price": {"type": "number"},
                            "in_price": {"type": "number"},
                            "stock": {"type": "integer"}
                        }
                    }
                },
                "pager": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer"},
                        "currentPage": {"type": "integer"},
                        "pageCount": {"type": "integer"},
                        "count": {"type": "integer"}
                    }
                }
            }
        }
    }
}

# STS 凭证响应
FILE_STS_RESPONSE = {
    "type": "object",
    "required": ["error", "data"],
    "properties": {
        "error": {"type": "integer", "enum": [0]},
        "data": {
            "type": "object",
            "required": ["Credentials"],
            "properties": {
                "Credentials": {
                    "type": "object",
                    "required": ["AccessKeyId", "AccessKeySecret", "SecurityToken", "Expiration"],
                    "properties": {
                        "AccessKeyId": {"type": "string", "pattern": "^STS\\."},
                        "AccessKeySecret": {"type": "string"},
                        "SecurityToken": {"type": "string"},
                        "Expiration": {"type": "string"}
                    }
                },
                "mode": {"type": "string", "enum": ["test", "prod", "dev"]}
            }
        }
    }
}

# 分类列表响应
CATEGORY_LIST_RESPONSE = {
    "type": "object",
    "required": ["error", "data"],
    "properties": {
        "error": {"type": "integer", "enum": [0]},
        "data": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["category_id", "name"],
                "properties": {
                    "category_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "parent_id": {"type": "integer"},
                    "level": {"type": "integer"}
                }
            }
        }
    }
}

# 供应商列表响应
SUPPLIER_LIST_RESPONSE = {
    "type": "object",
    "required": ["error", "data"],
    "properties": {
        "error": {"type": "integer", "enum": [0]},
        "data": {
            "type": "object",
            "required": ["list"],
            "properties": {
                "list": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["supplier_id", "name"],
                        "properties": {
                            "supplier_id": {"type": "integer"},
                            "name": {"type": "string"},
                            "phone": {"type": "string"}
                        }
                    }
                }
            }
        }
    }
}

# 计算入库价格响应
COMPUTE_IN_PRICE_RESPONSE = {
    "type": "object",
    "required": ["error", "data"],
    "properties": {
        "error": {"type": "integer", "enum": [0]},
        "data": {"type": "number"}
    }
}

# 批量操作成功响应
BATCH_SUCCESS_RESPONSE = {
    "type": "object",
    "required": ["error", "data"],
    "properties": {
        "error": {"type": "integer", "enum": [0]},
        "data": {"type": "string", "enum": ["success"]}
    }
}

# SPU 详情响应
SPU_DETAIL_RESPONSE = {
    "type": "object",
    "required": ["error", "data"],
    "properties": {
        "error": {"type": "integer", "enum": [0]},
        "data": {
            "type": "object",
            "required": ["spu_id", "name", "skus"],
            "properties": {
                "spu_id": {"type": "string"},
                "name": {"type": "string"},
                "detail": {"type": "string"},
                "stock": {"type": "integer"},
                "skus": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer"},
                            "name": {"type": "string"}
                        }
                    }
                }
            }
        }
    }
}
