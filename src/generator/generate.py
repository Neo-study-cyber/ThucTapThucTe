import os
import json
import re
import ollama

def clean_payload(line: str) -> str:
    """Xóa bỏ các đuôi rác hoặc nhãn định dạng thừa"""
    line = line.strip()
    line = re.sub(r',\s*\d+$', '', line)
    return line.strip()

def load_seeds():
    seed_path = "data/seed_sqli.json"
    if os.path.exists(seed_path):
        with open(seed_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return ["' OR '1'='1", "1' UNION SELECT NULL--", "admin' --", "' OR 'a'='a"]

def generate_payloads(seed_examples, target_num=250, attack_type="SQL Injection"):
    all_payloads = []
    batch_size = 40
    num_batches = (target_num // batch_size) + 1

    for i in range(num_batches):
        if len(all_payloads) >= target_num:
            break

        seeds_formatted = "\n".join([f"- {clean_payload(str(s))}" for s in seed_examples[:15]])

        prompt = f"""Ban la chuyen gia bao mat web.
Dưới đây là một số mẫu payload {attack_type} thật (seed examples):
{seeds_formatted}

Hãy sinh chính xác {batch_size} payload {attack_type} mới độc đáo, tinh vi, khác biệt so với các mẫu trên.
Yêu cầu:
- Mỗi payload nằm trên đúng một dòng.
- Không gắn số thứ tự, không chèn markdown codeblock, không ghi văn bản giải thích.
- Đa dạng các kỹ thuật: URL encoding, case variation, chèn comment, tautology, union-based, error-based.
- Tuyệt đối không thêm dấu phẩy hay số thứ tự ở cuối payload.
"""

        try:
            response = ollama.chat(
                model='qwen2.5:7b',
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'temperature': 0.7,
                    'num_predict': 4096
                }
            )
            content = response['message']['content'].strip()

            raw_lines = content.split('\n')
            for line in raw_lines:
                cleaned = clean_payload(line)
                if cleaned and not cleaned.startswith("```") and not cleaned.startswith("#") and "Here are" not in cleaned:
                    if cleaned not in all_payloads:
                        all_payloads.append(cleaned)
        except Exception as e:
            break

    return all_payloads[:target_num]

def main():
    os.makedirs("data", exist_ok=True)
    seeds = load_seeds()
    
    raw_payloads = generate_payloads(seeds, target_num=250, attack_type="SQL Injection")

    output_path = "data/raw_payloads.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(raw_payloads, f, ensure_ascii=False, indent=4)
    
    print(f"Da tao {len(raw_payloads)} payload. Duoc luu tai file: {output_path}")

if __name__ == "__main__":
    main()
