import os
import sys
import json
import time
import pandas as pd

# Import 5 lớp kiểm chứng
from pipeline.layer1_syntax import check_sql_syntax
from pipeline.layer2_validity import check_validity
from pipeline.layer3_execution import check_execution
from pipeline.layer4_diversity import DiversityChecker
from pipeline.layer5_llm_judge import llm_as_a_judge

def run_5_layer_pipeline(raw_payloads: list):
    """Quy trình kiểm chứng 5 lớp"""
    print("\n" + "=" * 65)
    print("[*] BẮT ĐẦU CHẠY PIPELINE KIỂM CHỨNG 5 LỚP")
    print("=" * 65)

    diversity_checker = DiversityChecker(similarity_threshold=0.85)
    final_validated_payloads = []

    stats = {"L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0}

    for idx, payload in enumerate(raw_payloads, 1):
        print(f"\n[*] Đang xử lý Payload [{idx}/{len(raw_payloads)}]: {payload[:50]}...")

        # Lớp 1: Cú pháp (sqlparse)
        if not check_sql_syntax(payload):
            print(" └─ [X] Bị loại ở Lớp 1 (Syntax sqlparse)")
            continue
        stats["L1"] += 1

        # Lớp 2: Hợp lệ (Malformed Check)
        if not check_validity(payload):
            print(" └─ [X] Bị loại ở Lớp 2 (Malformed/Invalid)")
            continue
        stats["L2"] += 1

        # Lớp 3: Thực thi (DVWA/WAF Check)
        exec_res = check_execution(payload)
        if not exec_res["passed"]:
            print(" └─ [X] Bị loại ở Lớp 3 (Execution Failure)")
            continue
        stats["L3"] += 1

        # Lớp 4: Độ đa dạng (SequenceMatcher)
        if not diversity_checker.is_diverse(payload):
            print(" └─ [X] Bị loại ở Lớp 4 (Trùng lặp/Tương đồng cao)")
            continue
        stats["L4"] += 1

        # Lớp 5: LLM-as-a-Judge (Gemini)
        if not llm_as_a_judge(payload):
            print(" └─ [X] Bị loại ở Lớp 5 (LLM Judge FAIL)")
            continue
        stats["L5"] += 1

        print(" └─ [✓] ĐẠT CHUẨN TẤT CẢ 5 LỚP!")
        final_validated_payloads.append(payload)

        # Tránh chạm Rate Limit của API Gemini Free Tier
        time.sleep(1.5)

    print("\n" + "=" * 65)
    print("[✓] THỐNG KÊ KẾT QUẢ QUA 5 LỚP KIỂM CHỨNG:")
    print(f" - Tổng đầu vào đưa vào          : {len(raw_payloads)}")
    print(f" - Qua Lớp 1 (Syntax sqlparse)  : {stats['L1']}")
    print(f" - Qua Lớp 2 (Validity Check)   : {stats['L2']}")
    print(f" - Qua Lớp 3 (Execution Check)  : {stats['L3']}")
    print(f" - Qua Lớp 4 (Diversity Check)  : {stats['L4']}")
    print(f" - Qua Lớp 5 (LLM-as-a-Judge)   : {stats['L5']}")
    print(f" => Tổng mẫu đạt chuẩn giữ lại : {len(final_validated_payloads)}")
    if len(raw_payloads) > 0:
        print(f" => Tỷ lệ đạt chuẩn (Pass Rate): {(len(final_validated_payloads) / len(raw_payloads))*100:.2f}%")
    print("=" * 65)

    return final_validated_payloads
5
def main():
    RAW_INPUT_FILE = "data/raw_payloads.json"
    OUTPUT_FILE = "data/final/validated_sqli.csv"

    # 1. Đọc dữ liệu thô từ file JSON
    if not os.path.exists(RAW_INPUT_FILE):
        print(f"[!] Không tìm thấy file dữ liệu thô tại: {RAW_INPUT_FILE}")
        print("[!] Vui lòng chạy `python src/test_generator.py` trước để sinh dữ liệu.")
        return

    with open(RAW_INPUT_FILE, "r", encoding="utf-8") as f:
        raw_payloads = json.load(f)

    print(f"[*] Đã nạp thành công {len(raw_payloads)} payload thô từ: {RAW_INPUT_FILE}")

    # 2. Chạy qua Pipeline 5 Lớp
    validated_payloads = run_5_layer_pipeline(raw_payloads)

    # 3. Lưu kết quả ra CSV
    if validated_payloads:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        df = pd.DataFrame({
            "payload": validated_payloads,
            "label": 1
        })
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
        print(f"\n[✓] ĐÃ LƯU SUCCESSFUL {len(validated_payloads)} PAYLOAD ĐẠT CHUẨN VÀO: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
