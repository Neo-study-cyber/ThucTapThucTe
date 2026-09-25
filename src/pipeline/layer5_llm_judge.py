import sys
import time
import ollama

# Tự động ép Terminal xử lý chuẩn UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def llm_as_a_judge(payload: str, model_name: str = "qwen2.5:7b", max_retries: int = 3) -> bool:
    """
    Lớp 5: LLM-as-a-Judge dùng Local LLM (Ollama) không giới hạn rate limit.
    """
    prompt = f"""You are an Expert Security Data Quality Auditor (LLM-as-a-Judge).
Evaluate the quality and validity of the following SQL Injection payload:

Payload: `{payload}`

Evaluation Requirements:
- Check if it is a structured SQL Injection payload.
- Reject if it is explanatory text, conversational response, or invalid format.

Respond with ONLY 'PASS' if it is a valid payload, or 'FAIL' if invalid. Do not include any other text.
"""
    for attempt in range(max_retries):
        try:
            response = ollama.chat(
                model=model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.1}
            )
            result = response['message']['content'].strip().upper()
            return "PASS" in result

        except Exception as e:
            print(f"[!] Lỗi Ollama Judge: {e}")
            time.sleep(2)

    return False
