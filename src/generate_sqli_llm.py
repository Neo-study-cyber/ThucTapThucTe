# src/generate_sqli_llm.py
import os
import json
import requests
import pandas as pd

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"  # Hoặc "qwen2.5" tùy theo model em đang cài trên máy

def load_seeds():
    seed_path = "data/seed_sqli.json"
    if os.path.exists(seed_path):
        with open(seed_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return ["' OR '1'='1", "1' UNION SELECT NULL--"]

def generate_payloads_with_llm(seeds, num_batches=5):
    all_generated = []
    print(f"[*] Đang kết nối tới Ollama ({MODEL_NAME}) để sinh dữ liệu...")

    for i in range(num_batches):
        # Lấy mẫu ngẫu nhiên vài seed làm ví dụ để LLM học theo phong cách
        prompt = f"""
Bạn là một chuyên gia kiểm thử xâm nhập (Penetration Tester). 
Dựa vào các mẫu SQL Injection sau đây:
{json.dumps(seeds[:5], ensure_ascii=False)}

Hãy tạo ra 30 mẫu payload SQL Injection mới, độc đáo, đa dạng (bao gồm Error-based, Union-based, Blind, Boolean-based).
YÊU CẦU QUAN TRỌNG: 
- Chỉ trả về danh sách các payload, mỗi payload nằm trên một dòng riêng biệt.
- KHÔNG giải thích, KHÔNG thêm đánh số thứ tự hay văn bản thừa thãi.
"""

        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7}
        }

        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json().get("response", "")
                lines = [line.strip() for line in result.split("\n") if line.strip()]
                all_generated.extend(lines)
                print(f" [+] Batch {i+1}/{num_batches}: Sinh thành công {len(lines)} mẫu.")
            else:
                print(f" [!] Lỗi từ Ollama API: {response.status_code}")
        except Exception as e:
            print(f" [!] Không thể kết nối đến Ollama (Hãy đảm bảo service Ollama đang chạy): {e}")
            break

    # Lọc bỏ trùng lặp
    unique_payloads = list(set(all_generated))
    return unique_payloads

def main():
    os.makedirs("data/final", exist_ok=True)
    seeds = load_seeds()
    
    # Sinh khoảng 5-10 batch (mỗi batch ~30 mẫu để thu về tầm 150-250 mẫu)
    raw_payloads = generate_payloads_with_llm(seeds, num_batches=6)
    print(f"[*] Tổng số payload thô sinh ra: {len(raw_payloads)}")

    # Lọc sơ bộ (loại bỏ các chuỗi quá ngắn hoặc quá dài bất thường)
    validated_payloads = [p for p in raw_payloads if 5 <= len(p) <= 200]
    print(f"[*] Số lượng sau khi lọc cơ bản: {len(validated_payloads)}")

    # Lưu vào file validated_sqli.csv để dùng cho Downstream Evaluation
    df_output = pd.DataFrame({
        'payload': validated_payloads,
        'label': [1] * len(validated_payloads)
    })
    
    output_path = "data/final/validated_sqli.csv"
    df_output.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[✓] Đã lưu thành công tập dữ liệu mới tại: {output_path} ({len(df_output)} mẫu).")

if __name__ == "__main__":
    main()
