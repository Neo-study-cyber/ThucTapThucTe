from google import genai

# Dán nguyên chuỗi key AQ... của bạn vào đây
API_KEY = "AQ.Ab8RN6LLG4ISOnA0rSZFvqGuKUN03b6snuJ7FUlLbzRlp8EK_Q"

try:
    client = genai.Client(api_key=API_KEY)
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents="Hãy phản hồi duy nhất chữ 'SUCCESS' nếu nhận được tin nhắn này."
    )
    print("Kết quả:", response.text.strip())
    print("[✓] API Key hoạt động hoàn hảo!")
except Exception as e:
    print("[X] Lỗi kiểm tra Key:", e)
