import requests
import json
import os
import sys

# Попытка прочитать API ключ из settings.json
api_key = ""
try:
    if os.path.exists("settings.json"):
        with open("settings.json", "r", encoding="utf-8") as f:
            import json
            settings = json.load(f)
            if "ai_api_key" in settings:
                api_key = settings["ai_api_key"]
                print(f"API ключ успешно загружен из settings.json")
except Exception as e:
    print(f"Ошибка при чтении settings.json: {e}")

API_KEY = api_key  # Используем ключ из settings.json
MODEL = "deepseek/deepseek-r1"

def process_content(content):
    return content.replace('<think>', '').replace('</think>', '')

def chat_stream(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True
    }

    with requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        stream=True
    ) as response:
        if response.status_code != 200:
            print("Ошибка API:", response.status_code)
            print("Текст ошибки:", response.text)
            return ""

        full_response = []
        
        for chunk in response.iter_lines():
            if chunk:
                chunk_str = chunk.decode('utf-8').replace('data: ', '')
                try:
                    chunk_json = json.loads(chunk_str)
                    if "choices" in chunk_json:
                        content = chunk_json["choices"][0]["delta"].get("content", "")
                        if content:
                            cleaned = process_content(content)
                            print(cleaned, end='', flush=True)
                            full_response.append(cleaned)
                except:
                    pass

        print()  # Перенос строки после завершения потока
        return ''.join(full_response)

def main():
    print("Чат с DeepSeek-R1 (by Antric)\nДля выхода введите 'exit'\n")
    print(f"API ключ установлен: {'Да' if API_KEY else 'Нет'}")

    while True:
        user_input = input("Вы: ")
        
        if user_input.lower() == 'exit':
            print("Завершение работы...")
            break
            
        print("DeepSeek-R1:", end=' ', flush=True)
        chat_stream(user_input)

if __name__ == "__main__":
    main()