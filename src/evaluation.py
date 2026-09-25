# src/evaluation.py
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

def main():
    REAL_DATA_PATH = "data/processed/http_params_cleaned.csv"
    LLM_DATA_PATH = "data/final/validated_sqli.csv"
    
    print("[*] Đang nạp dữ liệu cho quá trình Downstream Evaluation...")
    
    # 1. Nạp dữ liệu thật từ Tuần 1
    if not os.path.exists(REAL_DATA_PATH):
        print(f"[!] Không tìm thấy file dữ liệu thật tại: {REAL_DATA_PATH}")
        print("[!] Hãy chạy trước lệnh: python src/load_http_params.py")
        return
        
    df_real = pd.read_csv(REAL_DATA_PATH)
    
    # 2. Nạp dữ liệu LLM đã qua vòng kiểm chứng (Tuần 2-3)
    if not os.path.exists(LLM_DATA_PATH):
        print(f"[!] Không tìm thấy file dữ liệu LLM tại: {LLM_DATA_PATH}")
        return
        
    df_llm = pd.read_csv(LLM_DATA_PATH)

    # Tách chuỗi và nhãn của dữ liệu thật
    X_real = df_real['payload'].astype(str).tolist()
    y_real = df_real['label'].astype(int).tolist()

    # 3. Chia tập thật thành Train thật và Test chuẩn (Holdout Test Set)
    X_real_train, X_test, y_real_train, y_test = train_test_split(
        X_real, y_real, test_size=0.2, random_state=42, stratify=y_real
    )

    # Dữ liệu LLM (toàn bộ là payload tấn công nên nhãn là 1)
    X_llm = df_llm['payload'].astype(str).tolist()
    y_llm = [1] * len(X_llm)

    print(f" [+] Kích thước tập Test thực tế (Real Test) : {len(X_test)} mẫu")
    print(f" [+] Kích thước tập Train thật (Real Train): {len(X_real_train)} mẫu")
    print(f" [+] Kích thước tập LLM Validated (Synthetic): {len(X_llm)} mẫu\n")

    results = []

    # --- KỊCH BẢN 1: Chỉ dùng dữ liệu thật (Baseline) ---
    print("[*] Đang chạy Kịch bản 1: Chỉ dùng dữ liệu thật...")
    vectorizer_1 = TfidfVectorizer(analyzer='char', ngram_range=(2, 5))
    X_train_real_vec = vectorizer_1.fit_transform(X_real_train)
    X_test_vec_1 = vectorizer_1.transform(X_test)

    clf_1 = LogisticRegression(random_state=42, max_iter=1000)
    clf_1.fit(X_train_real_vec, y_real_train)
    y_pred_1 = clf_1.predict(X_test_vec_1)

    acc_1 = accuracy_score(y_test, y_pred_1)
    prec_1 = precision_score(y_test, y_pred_1, zero_division=0)
    rec_1 = recall_score(y_test, y_pred_1, zero_division=0)
    f1_1 = f1_score(y_test, y_pred_1, zero_division=0)

    results.append({"Scenario": "1. Chỉ dùng Dữ liệu Thật (Baseline)", "Accuracy": acc_1, "Precision": prec_1, "Recall": rec_1, "F1-score": f1_1})

    # --- KỊCH BẢN 2: Dữ liệu LLM SQLi kết hợp Benign Thật (Có class_weight='balanced') ---
    print("[*] Đang chạy Kịch bản 2: Dữ liệu LLM SQLi + Benign Thật...")
    X_real_train_benign = [x for x, y in zip(X_real_train, y_real_train) if y == 0]
    y_real_train_benign = [0] * len(X_real_train_benign)
    
    X_train_llm_scenario = X_llm + X_real_train_benign
    y_train_llm_scenario = y_llm + y_real_train_benign
    
    vectorizer_2 = TfidfVectorizer(analyzer='char', ngram_range=(2, 5))
    X_train_llm_vec = vectorizer_2.fit_transform(X_train_llm_scenario)
    X_test_llm_vec = vectorizer_2.transform(X_test)
    
    clf_2 = LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced')
    clf_2.fit(X_train_llm_vec, y_train_llm_scenario)
    y_pred_2 = clf_2.predict(X_test_llm_vec)
    
    acc_2 = accuracy_score(y_test, y_pred_2)
    prec_2 = precision_score(y_test, y_pred_2, zero_division=0)
    rec_2 = recall_score(y_test, y_pred_2, zero_division=0)
    f1_2 = f1_score(y_test, y_pred_2, zero_division=0)

    results.append({"Scenario": "2. Dữ liệu LLM SQLi + Benign Thật", "Accuracy": acc_2, "Precision": prec_2, "Recall": rec_2, "F1-score": f1_2})

    # --- KỊCH BẢN 3: Kết hợp Thật + LLM (Augmented) ---
    print("[*] Đang chạy Kịch bản 3: Kết hợp Thật + LLM (Augmented)...")
    X_combined = X_real_train + X_llm
    y_combined = y_real_train + y_llm
    
    vectorizer_3 = TfidfVectorizer(analyzer='char', ngram_range=(2, 5))
    X_train_combined_vec = vectorizer_3.fit_transform(X_combined)
    X_test_vec_3 = vectorizer_3.transform(X_test)
    
    clf_3 = LogisticRegression(random_state=42, max_iter=1000)
    clf_3.fit(X_train_combined_vec, y_combined)
    y_pred_3 = clf_3.predict(X_test_vec_3)
    
    acc_3 = accuracy_score(y_test, y_pred_3)
    prec_3 = precision_score(y_test, y_pred_3, zero_division=0)
    rec_3 = recall_score(y_test, y_pred_3, zero_division=0)
    f1_3 = f1_score(y_test, y_pred_3, zero_division=0)

    results.append({"Scenario": "3. Kết hợp Thật + LLM (Augmented)", "Accuracy": acc_3, "Precision": prec_3, "Recall": rec_3, "F1-score": f1_3})

    # 5. Xuất bảng tổng kết kết quả
    df_results = pd.DataFrame(results)
    print("\n" + "=" * 80)
    print(" BẢNG TỔNG KẾT ĐÁNH GIÁ (DOWNSTREAM EVALUATION SUMMARY)")
    print("=" * 80)
    print(df_results.to_string(index=False))
    print("=" * 80)

if __name__ == "__main__":
    main()

