"""
Schema Context Manager
Quản lý schema name trong request context sử dụng contextvars
"""
from contextvars import ContextVar
from typing import Optional

# Context variable để lưu schema name
_schema_context: ContextVar[Optional[str]] = ContextVar(
    'schema_name', 
    default=None
)

def get_current_schema() -> Optional[str]:
    """
    Lấy schema name từ context
    
    Returns:
        Schema name hoặc None nếu chưa đăng nhập
    """
    return _schema_context.get()

def set_current_schema(schema: Optional[str]) -> None:
    """
    Set schema name vào context
    
    Args:
        schema: Schema name hoặc None
    """
    _schema_context.set(schema)

def has_schema() -> bool:
    """
    Check xem có schema (đã đăng nhập) chưa
    
    Returns:
        True nếu có schema, False nếu chưa đăng nhập
    """
    return _schema_context.get() is not None

def clear_schema() -> None:
    """Clear schema từ context"""
    _schema_context.set(None)

