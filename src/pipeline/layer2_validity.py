import re

def check_validity(payload: str) -> bool:
    """
    Lớp 2: Loại bỏ payload malformed, ký tự điều khiển rác, hoặc lỗi mã hóa.
    """
    if not payload or len(payload.strip()) < 3 or len(payload) > 2000:
        return False
    
    # Lọc các ký tự điều khiển ASCII không in được (như Null Byte \x00)
    if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', payload):
        return False
        
    # Kiểm tra tính toàn vẹn của chuỗi UTF-8
    try:
        payload.encode('utf-8').decode('utf-8')
    except UnicodeError:
        return False

    return True
