import re
import time
from openai import OpenAI
from config import (
    OPENROUTER_API_KEY, MODEL, BASE_URL,
    INPUT_FILE_PATH, OUTPUT_FILE_PATH,
    MESSAGE_PREFIX, DELAY_BETWEEN_REQUESTS, DEBUG
)


def save_to_file(original_line, llm_response):
    """
    Сохраняет результат в файл (открывает и закрывает файл каждый раз)

    Args:
        original_line: Исходная строка из входного файла
        llm_response: Ответ от LLM
    """
    with open(OUTPUT_FILE_PATH, 'a', encoding='utf-8') as output_file:
        output_file.write(f"Исходная строка: {original_line}\n")
        output_file.write(f"Ответ LLM: {llm_response}\n")
        output_file.write("-" * 80 + "\n\n")


def process_file():
    """
    Обрабатывает файл построчно с сохранением результатов после каждого запроса
    """

    # Инициализация клиента OpenAI для работы с OpenRouter
    client = OpenAI(
        base_url=BASE_URL,
        api_key=OPENROUTER_API_KEY
    )

    # Регулярное выражение для проверки строки, начинающейся с числа
    pattern = r'^\d+\.\s*(.+)$'

    # Счетчики и статистика
    request_count = 0
    response_times = []

    # Считаем количество строк для обработки (для прогресса)
    try:
        with open(INPUT_FILE_PATH, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()

        # Фильтруем только строки, начинающиеся с числа
        lines_to_process = [line.strip() for line in all_lines if re.match(pattern, line.strip())]
        total_lines = len(lines_to_process)

        print(f"📄 Найдено {total_lines} строк для обработки из {len(all_lines)} всего")

        if DEBUG:
            print("⚠️  РЕЖИМ ОТЛАДКИ ВКЛЮЧЕН: программа завершится после 3 запросов")

        # Начало отсчета общего времени
        t_start = time.perf_counter()

        # Обработка каждой строки
        for line_num, line in enumerate(lines_to_process, 1):
            # Проверка режима отладки
            if DEBUG and request_count >= 3:
                print(f"\n🛑 DEBUG: Достигнут лимит в 3 запроса. Программа завершается.")
                break

            match = re.match(pattern, line)
            if match:
                # Извлекаем текст без номера
                text_without_number = match.group(1)

                print(f"\n{'=' * 60}")
                print(f"📝 Обработка строки {line_num}/{total_lines}")
                print(f"Текст: {line[:80]}...")

                # Формируем полное сообщение для LLM
                full_message = MESSAGE_PREFIX + text_without_number

                try:
                    # Замер времени запроса
                    t_req_start = time.perf_counter()

                    # Отправляем запрос к LLM
                    response = client.chat.completions.create(
                        model=MODEL,
                        messages=[
                            {"role": "user", "content": full_message}
                        ]
                    )

                    # Вычисляем время ответа
                    t_req_end = time.perf_counter()
                    last_response_time = t_req_end - t_req_start
                    response_times.append(last_response_time)
                    request_count += 1

                    # Получаем ответ
                    llm_response = response.choices[0].message.content

                    # Сохраняем в файл (файл открывается и закрывается)
                    save_to_file(line, llm_response)

                    # Статистика
                    print(f"✅ Ответ получен и сохранен")
                    print(f"⏱️  Время ответа: {last_response_time:.2f} сек")

                    # Прогресс и прогноз
                    percent_done = (request_count / total_lines) * 100
                    avg_time = sum(response_times) / len(response_times)
                    left_queries = total_lines - request_count
                    eta = left_queries * (avg_time + DELAY_BETWEEN_REQUESTS)
                    total_elapsed = time.perf_counter() - t_start

                    print(f"📊 Прогресс: {percent_done:.1f}% ({request_count}/{total_lines})")
                    print(f"⏰ Общее время работы: {total_elapsed:.2f} сек")
                    print(f"📈 Среднее время ответа: {avg_time:.2f} сек")
                    print(f"⏳ Прогноз оставшегося времени: {eta:.2f} сек ({eta / 60:.1f} мин)")

                    # Задержка между запросами (не применяется после последнего запроса)
                    if request_count < total_lines and not (DEBUG and request_count >= 3):
                        print(f"💤 Ожидание {DELAY_BETWEEN_REQUESTS} секунд перед следующим запросом...")
                        time.sleep(DELAY_BETWEEN_REQUESTS)

                except Exception as e:
                    error_msg = f"Ошибка при обращении к LLM: {e}"
                    print(f"❌ {error_msg}")

                    # Сохраняем ошибку в файл
                    save_to_file(line, f"ОШИБКА: {error_msg}")

        # Финальная статистика
        total_time = time.perf_counter() - t_start
        print(f"\n{'=' * 60}")
        print(f"✅ Обработка завершена!")
        print(f"📊 Всего обработано запросов: {request_count} из {total_lines}")
        print(f"⏰ Общее время работы: {total_time:.2f} сек ({total_time / 60:.1f} мин)")

        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            print(f"📈 Среднее время ответа: {avg_response_time:.2f} сек")
            print(f"⚡ Самый быстрый ответ: {min_time:.2f} сек")
            print(f"🐌 Самый медленный ответ: {max_time:.2f} сек")

        print(f"💾 Результаты сохранены в: {OUTPUT_FILE_PATH}")

    except FileNotFoundError:
        print(f"❌ Ошибка: Файл {INPUT_FILE_PATH} не найден!")
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")


if __name__ == "__main__":
    process_file()
