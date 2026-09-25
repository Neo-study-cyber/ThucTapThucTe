import sqlparse

def check_sql_syntax(payload: str) -> bool:
    """
    Lớp 1: Kiểm tra cú pháp bằng sqlparse.
    """
    if not payload or not isinstance(payload, str):
        return False
    
    parsed = sqlparse.parse(payload)
    if not parsed:
        return False
    
    # Kiểm tra xem chuỗi có chứa cây token cấu trúc SQL hay không
    for statement in parsed:
        if len(statement.tokens) > 0:
            return True
            
    return False
