import json
import os
from generator.generate import generate_payloads
from validator.validate import PayloadValidator

def main():
    print("="*60)
    print(" CHẠY PIPELINE SINH VÀ LỌC DỮ LIỆU SQL INJECTION")
    print("="*60)

    # 1. Load seed data
    seed_path = "data/seed_sqli.json"
    with open(seed_path, "r", encoding="utf-8") as f:
        seed_data = json.load(f)
    print(f"[1] Nạp thành công {len(seed_data)} mẫu seed data.")

    # 2. Sinh dữ liệu thô
    print("\n[2] Đang gọi LLM (qwen2.5:7b) sinh 100 payload thô...")
    raw_payloads = generate_payloads(seed_data, num_payloads=100, attack_type="SQL Injection")
    print(f" -> Thu được {len(raw_payloads)} payload thô ban đầu.")

    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/raw_sqli.json", "w", encoding="utf-8") as f:
        json.dump(raw_payloads, f, indent=2, ensure_ascii=False)

    # 3. Validation Loop
    print("\n[3] Bắt đầu Vòng kiểm chứng 5 Lớp...")
    validator = PayloadValidator(dvwa_url="http://localhost", similarity_threshold=0.75)
    high_quality_payloads = validator.validate_pipeline(raw_payloads, seed_data)

    # In log chi tiết phục vụ viết báo cáo
    s = validator.stats
    total_raw = len(raw_payloads)
    total_clean = len(high_quality_payloads)

    print("\n" + "="*45)
    print(" BẢNG THỐNG KÊ TỶ LỆ LOẠI BỎ (REJECTION RATE)")
    print("="*45)
    print(f"- Lớp 1 (Syntax Check - sqlparse) : Bị loại {s['layer1_syntax']}")
    print(f"- Lớp 2 (Validity Check)          : Bị loại {s['layer2_validity']}")
    print(f"- Lớp 3 (DVWA Execution Check)    : Bị loại {s['layer3_exploit']}")
    print(f"- Lớp 4 (Diversity Check)         : Bị loại {s['layer4_diversity']}")
    print(f"- Lớp 5 (LLM-as-a-Judge Score)    : Bị loại {s['layer5_judge']}")
    print("-" * 45)
    rate = (total_clean / total_raw * 100) if total_raw > 0 else 0
    print(f" -> TỔNG ĐẠT CHUẨN                : {total_clean}/{total_raw} ({rate:.1f}%)")

    # 4. Lưu kết quả final
    os.makedirs("data/final", exist_ok=True)
    final_path = "data/final/high_quality_sqli.json"
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(high_quality_payloads, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] Đã lưu dữ liệu chất lượng cao vào: {final_path}")

if __name__ == "__main__":
    main()
