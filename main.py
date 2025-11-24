import re
import time
from openai import OpenAI
from config import (
    OPENROUTER_API_KEY, MODEL, BASE_URL,
    INPUT_FILE_PATH, OUTPUT_FILE_PATH,
    MESSAGE_PREFIX, DELAY_BETWEEN_REQUESTS, DEBUG
)


def process_file():
    client = OpenAI(
        base_url=BASE_URL,
        api_key=OPENROUTER_API_KEY
    )
    pattern = r'^\d+\.\s*(.+)$'
    request_count = 0
    total_lines = 0
    response_times = []
    last_response_time = 0

    # Считаем кол-во строк, для прогресса
    with open(INPUT_FILE_PATH, 'r', encoding='utf-8') as f:
        lines_all = f.readlines()
    lines = [line.strip() for line in lines_all if re.match(pattern, line.strip())]
    total_lines = len(lines)

    t_start = time.perf_counter()  # Общее время начала

    with open(OUTPUT_FILE_PATH, 'a', encoding='utf-8') as output_file:
        for line_num, line in enumerate(lines, 1):
            if DEBUG and request_count >= 3:
                print(f"\n🛑 DEBUG: Достигнут лимит в 3 запроса. Программа завершается.")
                break

            match = re.match(pattern, line)
            if match:
                text_without_number = match.group(1)
                full_message = MESSAGE_PREFIX + text_without_number

                t_req_start = time.perf_counter()
                try:
                    response = client.chat.completions.create(
                        model=MODEL,
                        messages=[{"role": "user", "content": full_message}]
                    )
                    t_req_end = time.perf_counter()
                    last_response_time = t_req_end - t_req_start
                    response_times.append(last_response_time)
                    request_count += 1

                    llm_response = response.choices[0].message.content
                    output_file.write(f"Исходная строка: {line}\n")
                    output_file.write(f"Ответ LLM: {llm_response}\n")
                    output_file.write("-" * 80 + "\n\n")
                    print(f"\nСтрока {line_num}/{total_lines} обработана.")
                    print(f"Время ответа: {last_response_time:.2f} сек")

                    # Прогресс
                    percent_done = (request_count / total_lines) * 100
                    avg_time = sum(response_times) / len(response_times)
                    left_queries = total_lines - request_count
                    eta = left_queries * avg_time
                    total_elapsed = time.perf_counter() - t_start

                    print(f"Общий прогресс: {percent_done:.1f}%")
                    print(f"Общее время работы: {total_elapsed:.2f} сек")
                    print(f"Осталось запросов: {left_queries}, прогноз времени: {eta:.2f} сек")

                    if not (DEBUG and request_count >= 3):
                        print(f"⏳ Ожидание {DELAY_BETWEEN_REQUESTS} секунд ...")
                        time.sleep(DELAY_BETWEEN_REQUESTS)
                except Exception as e:
                    print(f"Ошибка на строке {line_num}: {e}")

    total_time = time.perf_counter() - t_start
    print(f"\n✅ Обработка завершена.")
    print(f"Всего запросов: {request_count} из {total_lines}")
    print(f"Общее время: {total_time:.2f} сек")
    if response_times:
        print(f"Среднее время ответа: {sum(response_times) / len(response_times):.2f} сек")

if __name__ == "__main__":
    process_file()
