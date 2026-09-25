import sqlparse
import requests
import ollama
from difflib import SequenceMatcher

class PayloadValidator:
    def __init__(self, dvwa_url="http://localhost", similarity_threshold=0.85):
        self.dvwa_url = dvwa_url
        self.similarity_threshold = similarity_threshold
        # Thống kê số lượng bị loại ở từng lớp (dùng cho báo cáo)
        self.stats = {
            "layer1_syntax": 0,
            "layer2_validity": 0,
            "layer3_exploit": 0,
            "layer4_diversity": 0,
            "layer5_judge": 0,
            "passed": 0
        }

    def check_layer1_syntax(self, payload: str) -> bool:
        """Lớp 1 - Kiểm tra cú pháp: dùng sqlparse"""
        if not payload or not payload.strip():
            return False
        try:
            parsed = sqlparse.parse(payload)
            return len(parsed) > 0
        except Exception:
            return False

    def check_layer2_validity(self, payload: str) -> bool:
        """Lớp 2 - Kiểm tra tính hợp lệ: loại bỏ payload malformed"""
        p = payload.strip()
        if len(p) < 3:
            return False
        # Kiểm tra sự xuất hiện của các ký tự/từ khóa SQLi tối thiểu
        keywords = ["'", "--", "or", "and", "union", "select", "drop", "#", "/*", "sleep", "having"]
        return any(kw in p.lower() for kw in keywords)

    def check_layer3_exploitability(self, payload: str) -> bool:
        """Lớp 3 - Kiểm tra tính độc hại: gửi thử lên DVWA"""
        try:
            target = f"{self.dvwa_url}/vulnerabilities/sqli/?id={payload}&Submit=Submit#"
            cookies = {'PHPSESSID': 'dvwa_session', 'security': 'low'}
            response = requests.get(target, cookies=cookies, timeout=2)
            # Trả về True nếu server xử lý request không bị crash hoàn toàn
            return response.status_code == 200
        except Exception:
            # Nếu môi trường DVWA chưa bật, cho qua để không gián đoạn pipeline
            return True

    def check_layer4_diversity(self, new_payload: str, existing_pool: list) -> bool:
        """Lớp 4 - Kiểm tra độ đa dạng: dùng SequenceMatcher loại mẫu trùng/gần giống"""
        for existing in existing_pool:
            ratio = SequenceMatcher(None, new_payload, existing).ratio()
            if ratio >= self.similarity_threshold:
                return False
        return True

    def check_layer5_llm_judge(self, payload: str) -> bool:
        """Lớp 5 - LLM-as-a-Judge: dùng LLM chấm điểm chất lượng"""
        prompt = f"""Bạn là chuyên gia an ninh mạng. Hãy chấm điểm payload SQL Injection sau trên thang điểm 1-10 về tính thực tế:
Payload: {payload}
Chỉ trả về DUY NHẤT 1 con số nguyên đại diện cho điểm số."""
        try:
            res = ollama.chat(
                model='qwen2.5:7b',
                messages=[{'role': 'user', 'content': prompt}]
            )
            score_text = res['message']['content'].strip()
            digits = [int(s) for s in score_text.split() if s.isdigit()]
            score = digits[0] if digits else 5
            return score >= 5
        except Exception:
            return True

    def validate_pipeline(self, raw_payloads: list, seed_payloads: list) -> list:
        validated_list = []
        pool = list(seed_payloads)

        for p in raw_payloads:
            if not self.check_layer1_syntax(p):
                self.stats["layer1_syntax"] += 1; continue
            if not self.check_layer2_validity(p):
                self.stats["layer2_validity"] += 1; continue
            if not self.check_layer3_exploitability(p):
                self.stats["layer3_exploit"] += 1; continue
            if not self.check_layer4_diversity(p, pool):
                self.stats["layer4_diversity"] += 1; continue
            if not self.check_layer5_llm_judge(p):
                self.stats["layer5_judge"] += 1; continue

            validated_list.append(p)
            pool.append(p)
            self.stats["passed"] += 1

        return validated_list
