import json
import os
import sys
import random
import pandas as pd

# Đảm bảo import đúng module generator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.generator.generate import generate_payloads

def load_morzeux_dataset(file_path: str) -> list:
    """Đọc file CSV từ HttpParamsDataset và lọc các mẫu SQL Injection"""
    if not os.path.exists(file_path):
        print(f"[!] Không tìm thấy file dataset tại: {file_path}")
        return []

    try:
        df = pd.read_csv(file_path)
        payload_col = "payload" if "payload" in df.columns else df.columns[0]
        type_col = "type" if "type" in df.columns else ("label" if "label" in df.columns else None)

        if type_col:
            sqli_df = df[df[type_col].astype(str).str.lower().str.contains("sqli", na=False)]
        else:
            sqli_df = df

        payloads = sqli_df[payload_col].dropna().astype(str).str.strip().tolist()
        return [p for p in payloads if len(p) > 2]
    except Exception as e:
        print(f"[!] Lỗi khi đọc HttpParamsDataset: {e}")
        return []

def run_generator_in_batches():
    SEED_DATASET_FILE = "data/HttpParamsDataset/payload_train.csv"
    RAW_OUTPUT_FILE = "data/raw_payloads.json"
    
    TARGET_TOTAL = 30   # Số mẫu thô mới muốn sinh
    BATCH_SIZE = 10      # Số mẫu sinh mỗi đợt

    # 1. Nạp kho seed từ Morzeux Dataset
    full_seed_bank = load_morzeux_dataset(SEED_DATASET_FILE)
    if not full_seed_bank:
        full_seed_bank = [
            "1' UNION SELECT null, username, password FROM users--",
            "' OR '1'='1",
            "1' AND SLEEP(5)--"
        ]

    # 2. KHỞI TẠO TẬP DỮ LIỆU MỚI TỪ ĐẦU (Xóa/Bỏ qua dữ liệu cũ)
    all_payloads = []

    print(f"[*] BẮT ĐẦU SINH LẠI TẬP DỮ LIỆU MỚI HOÀN TOÀN (TARGET: {TARGET_TOTAL} MẪU)...")
    
    batch_count = 1
    while len(all_payloads) < TARGET_TOTAL:
        sample_size = min(len(full_seed_bank), 8)
        current_seed_examples = random.sample(full_seed_bank, k=sample_size)

        print(f"\n--- Đợt {batch_count}: Sinh {BATCH_SIZE} payload (Tiến độ: {len(all_payloads)}/{TARGET_TOTAL}) ---")
        
        new_batch = generate_payloads(
            seed_examples=current_seed_examples, 
            num_payloads=BATCH_SIZE, 
            attack_type="SQL Injection"
        )

        if not new_batch:
            print("[!] Đợt này Ollama không trả về mẫu hợp lệ, đang thử lại...")
            continue

        before_count = len(all_payloads)
        for p in new_batch:
            if p not in all_payloads:
                all_payloads.append(p)

        added = len(all_payloads) - before_count
        print(f"[✓] Đợt {batch_count} thu được {len(new_batch)} mẫu thô -> Thêm {added} mẫu mới.")

        # Lưu ghi đè ("w") liên tục
        os.makedirs(os.path.dirname(RAW_OUTPUT_FILE), exist_ok=True)
        with open(RAW_OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_payloads, f, ensure_ascii=False, indent=2)

        batch_count += 1

    print("\n" + "=" * 65)
    print(f"[✓] HOÀN THÀNH! Đã tạo mới hoàn toàn {len(all_payloads)} payload thô.")
    print(f"[✓] File lưu tại: {RAW_OUTPUT_FILE}")
    print("=" * 65)

if __name__ == "__main__":
    run_generator_in_batches()
