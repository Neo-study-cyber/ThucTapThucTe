from difflib import SequenceMatcher

class DiversityChecker:
    """
    Lớp 4: Kiểm tra độ đa dạng bằng SequenceMatcher.
    """
    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self.accepted_payloads = []

    def is_diverse(self, payload: str) -> bool:
        for existing in self.accepted_payloads:
            # Tính độ tương đồng giữa payload mới và các mẫu đã chấp nhận
            sim = SequenceMatcher(None, payload, existing).ratio()
            if sim >= self.threshold:
                return False  # Quá giống mẫu đã có
        
        self.accepted_payloads.append(payload)
        return True
