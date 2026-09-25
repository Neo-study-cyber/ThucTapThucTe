import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def run_downstream_evaluation():
    # 1. Load Dữ liệu
    with open("data/seed_sqli.json", "r", encoding="utf-8") as f:
        real_sqli = json.load(f)

    final_path = "data/final/high_quality_sqli.json"
    if not os.path.exists(final_path):
        print("[!] Không tìm thấy file data/final/high_quality_sqli.json. Hãy chạy src/main.py trước!")
        return

    with open(final_path, "r", encoding="utf-8") as f:
        llm_sqli = json.load(f)

    # Tập dữ liệu lành tính (Benign samples)
    benign_samples = [
        "GET /index.php?page=home HTTP/1.1",
        "SELECT * FROM products WHERE category = 'books'",
        "user_login_status_ok",
        "search_query=thiet+bi+mang",
        "id=1020&type=json",
        "username=nguyenhoangngocduy&role=student",
        "api/v1/get_user_info?id=55",
        "ORDER BY price ASC",
        "SET NAMES 'utf8'",
        "GET /about-us HTTP/1.1",
        "POST /contact/submit HTTP/1.1",
        "SELECT id, title FROM posts WHERE status = 'published'"
    ]

    # Split tập dữ liệu thật thành Train và Test (Test cố định chỉ dùng dữ liệu thật)
    split_idx = int(len(real_sqli) * 0.7)
    train_real_sqli = real_sqli[:split_idx]
    test_real_sqli = real_sqli[split_idx:]

    train_benign = benign_samples[:8]
    test_benign = benign_samples[8:]

    X_test = test_real_sqli + test_benign
    y_test = [1]*len(test_real_sqli) + [0]*len(test_benign)

    # -------------------------------------------------------------
    # Trường hợp 1: Chỉ dùng Dữ liệu Thật (Real Only)
    # -------------------------------------------------------------
    X_train_1 = train_real_sqli + train_benign
    y_train_1 = [1]*len(train_real_sqli) + [0]*len(train_benign)

    vec1 = TfidfVectorizer(analyzer='char', ngram_range=(1, 3))
    X_tr1 = vec1.fit_transform(X_train_1)
    X_te1 = vec1.transform(X_test)
    clf1 = LogisticRegression().fit(X_tr1, y_train_1)
    p1 = clf1.predict(X_te1)

    # -------------------------------------------------------------
    # Trường hợp 2: Chỉ dùng Dữ liệu LLM (LLM Only - sau validation)
    # -------------------------------------------------------------
    X_train_2 = llm_sqli + train_benign
    y_train_2 = [1]*len(llm_sqli) + [0]*len(train_benign)

    vec2 = TfidfVectorizer(analyzer='char', ngram_range=(1, 3))
    X_tr2 = vec2.fit_transform(X_train_2)
    X_te2 = vec2.transform(X_test)
    clf2 = LogisticRegression().fit(X_tr2, y_train_2)
    p2 = clf2.predict(X_te2)

    # -------------------------------------------------------------
    # Trường hợp 3: Kết hợp Dữ liệu Thật + Dữ liệu LLM (Real + LLM)
    # -------------------------------------------------------------
    X_train_3 = train_real_sqli + llm_sqli + train_benign
    y_train_3 = [1]*(len(train_real_sqli) + len(llm_sqli)) + [0]*len(train_benign)

    vec3 = TfidfVectorizer(analyzer='char', ngram_range=(1, 3))
    X_tr3 = vec3.fit_transform(X_train_3)
    X_te3 = vec3.transform(X_test)
    clf3 = LogisticRegression().fit(X_tr3, y_train_3)
    p3 = clf3.predict(X_te3)

    # In Bảng So Sánh Chỉ Số
    print("\n" + "="*65)
    print(" KẾT QUẢ THÍ NGHIỆM DOWNSTREAM EVALUATION (SO SÁNH 3 TRƯỜNG HỢP)")
    print("="*65)
    print(f"{'Kịch Bản Huấn Luyện':<30} | {'Accuracy':<8} | {'Precision':<9} | {'Recall':<8} | {'F1-Score':<8}")
    print("-" * 65)

    def print_metrics(name, y_true, y_pred):
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        print(f"{name:<30} | {acc:<8.4f} | {prec:<9.4f} | {rec:<8.4f} | {f1:<8.4f}")

    print_metrics("1. Chỉ dùng dữ liệu thật", y_test, p1)
    print_metrics("2. Chỉ dùng dữ liệu LLM", y_test, p2)
    print_metrics("3. Kết hợp Thật + LLM", y_test, p3)
    print("="*65)

if __name__ == "__main__":
    run_downstream_evaluation()
