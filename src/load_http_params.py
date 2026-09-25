import os
import json
import pandas as pd

def process_http_params_dataset():
    dataset_dir = "data/HttpParamsDataset"
    
    # Kiểm tra xem folder đã clone về chưa
    if not os.path.exists(dataset_dir):
        print(f"[!] Không tìm thấy thư mục {dataset_dir}. Vui lòng chạy lệnh:")
        print("    git clone https://github.com/Morzeux/HttpParamsDataset.git data/HttpParamsDataset")
        return

    print("[*] Đang đọc các file dữ liệu từ HttpParamsDataset...")
    
    # Tìm tất cả file CSV/JSON trong thư mục đã clone
    all_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(dataset_dir) for f in filenames if f.endswith('.csv')]
    
    if not all_files:
        print("[!] Không tìm thấy file CSV nào trong dataset.")
        return

    dfs = []
    for f in all_files:
        try:
            # Thử đọc CSV với các delimiter phổ biến
            df_temp = pd.read_csv(f, on_bad_lines='skip')
            dfs.append(df_temp)
        except Exception as e:
            continue

    if not dfs:
        print("[!] Không thể đọc dữ liệu từ các file CSV.")
        return

    df = pd.concat(dfs, ignore_index=True)
    print(f"[✓] Đã nạp thành công {len(df)} dòng dữ liệu.")
    print("[*] Các cột dữ liệu tìm thấy:", df.columns.tolist())

    # Xác định các cột chứa Payload và Label
    payload_col = None
    for col in df.columns:
        if any(k in col.lower() for k in ['payload', 'value', 'data', 'param', 'text']):
            payload_col = col
            break
    if not payload_col:
        payload_col = df.columns[0]

    label_col = None
    for col in df.columns:
        if any(k in col.lower() for k in ['type', 'label', 'class', 'category', 'is_attack']):
            label_col = col
            break

    print(f" -> Cột Payload chọn: '{payload_col}'")
    print(f" -> Cột Label chọn: '{label_col}'")

    # Tách dữ liệu SQL Injection và Benign
    if label_col:
        sqli_df = df[df[label_col].astype(str).str.lower().str.contains('sqli|sql', na=False)]
        benign_df = df[df[label_col].astype(str).str.lower().str.contains('valid|benign|norm|0|false', na=False)]
    else:
        # Trường hợp không thấy cột label rõ ràng, lọc theo từ khóa SQLi
        sqli_mask = df[payload_col].astype(str).str.contains(r"UNION|SELECT|OR|AND|'|--", case=False, na=False)
        sqli_df = df[sqli_mask]
        benign_df = df[~sqli_mask]

    sqli_payloads = sqli_df[payload_col].dropna().astype(str).unique().tolist()
    benign_payloads = benign_df[payload_col].dropna().astype(str).unique().tolist()

    print(f" - Tìm thấy {len(sqli_payloads)} mẫu SQLi.")
    print(f" - Tìm thấy {len(benign_payloads)} mẫu Benign.")

    # 1. Trích xuất 30 mẫu SQLi làm Seed Data
    seed_data = sqli_payloads[:30] if sqli_payloads else ["' OR '1'='1", "1' UNION SELECT NULL--"]
    with open("data/seed_sqli.json", "w", encoding="utf-8") as f:
        json.dump(seed_data, f, indent=2, ensure_ascii=False)
    print(f"[✓] Đã lưu data/seed_sqli.json ({len(seed_data)} mẫu).")

    # 2. Trích xuất 200 mẫu Benign
    benign_data = benign_payloads[:200] if benign_payloads else ["GET /index.php?id=1", "page=home"]
    with open("data/benign_requests.json", "w", encoding="utf-8") as f:
        json.dump(benign_data, f, indent=2, ensure_ascii=False)
    print(f"[✓] Đã lưu data/benign_requests.json ({len(benign_data)} mẫu).")

    # 3. [BỔ SUNG QUAN TRỌNG CHO BƯỚC 5]: Tạo file CSV chuẩn hóa chứa cả SQLi (1) và Benign (0)
    os.makedirs("data/processed", exist_ok=True)
    
    # Lấy một lượng cân bằng (ví dụ: tối đa 500 mẫu mỗi loại để huấn luyện nhanh và mượt)
    max_samples = 500
    selected_sqli = sqli_payloads[:max_samples]
    selected_benign = benign_payloads[:max_samples]

    df_cleaned = pd.DataFrame({
        'payload': selected_sqli + selected_benign,
        'label': [1] * len(selected_sqli) + [0] * len(selected_benign)
    })
    
    csv_output_path = "data/processed/http_params_cleaned.csv"
    df_cleaned.to_csv(csv_output_path, index=False, encoding="utf-8")
    print(f"[✓] Đã tạo file dữ liệu sạch cho Downstream Evaluation tại: {csv_output_path} ({len(df_cleaned)} dòng).")# 3. [BỔ SUNG QUAN TRỌNG CHO BƯỚC 5]: Tạo file CSV chuẩn hóa chứa cả SQLi (1) và Benign (0)
    os.makedirs("data/processed", exist_ok=True)
    
    # Lấy một lượng cân bằng (ví dụ: tối đa 500 mẫu mỗi loại để huấn luyện nhanh và mượt)
    max_samples = 500
    selected_sqli = sqli_payloads[:max_samples]
    selected_benign = benign_payloads[:max_samples]

    df_cleaned = pd.DataFrame({
        'payload': selected_sqli + selected_benign,
        'label': [1] * len(selected_sqli) + [0] * len(selected_benign)
    })
    
    csv_output_path = "data/processed/http_params_cleaned.csv"
    df_cleaned.to_csv(csv_output_path, index=False, encoding="utf-8")
    print(f"[✓] Đã tạo file dữ liệu sạch cho Downstream Evaluation tại: {csv_output_path} ({len(df_cleaned)} dòng).")

if __name__ == "__main__":
    process_http_params_dataset()
