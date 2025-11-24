import re
import time
from openai import OpenAI
from config import (
    OPENROUTER_API_KEY,
    MODEL,
    BASE_URL,
    INPUT_FILE_PATH,
    OUTPUT_FILE_PATH,
    MESSAGE_PREFIX,
    DELAY_BETWEEN_REQUESTS,
    DEBUG
)


def process_file():
    """
    Обрабатывает файл построчно:
    1. Читает строки из входного файла
    2. Проверяет, начинается ли строка с числа
    3. Если да - убирает число, точку и пробел, отправляет в LLM
    4. Записывает исходную строку и ответ LLM в выходной файл
    5. Добавляет задержку между запросами
    6. В режиме DEBUG завершается после 3 запросов
    """

    # Инициализация клиента OpenAI для работы с OpenRouter
    client = OpenAI(
        base_url=BASE_URL,
        api_key=OPENROUTER_API_KEY
    )

    # Регулярное выражение для проверки строки, начинающейся с числа
    pattern = r'^\d+\.\s*(.+)$'

    # Счетчик обработанных запросов
    request_count = 0

    try:
        # Открываем входной файл для чтения
        with open(INPUT_FILE_PATH, 'r', encoding='utf-8') as input_file:
            lines = input_file.readlines()

        print(f"Прочитано {len(lines)} строк из файла {INPUT_FILE_PATH}")

        if DEBUG:
            print("⚠️  РЕЖИМ ОТЛАДКИ ВКЛЮЧЕН: программа завершится после 3 запросов")

        # Открываем выходной файл для записи (дозапись)
        with open(OUTPUT_FILE_PATH, 'a', encoding='utf-8') as output_file:

            for line_num, line in enumerate(lines, 1):
                line = line.strip()  # Убираем лишние пробелы и переносы строк

                # Пропускаем пустые строки
                if not line:
                    continue

                # Проверяем, начинается ли строка с числа
                match = re.match(pattern, line)

                if match:
                    # Проверка режима отладки
                    if DEBUG and request_count >= 3:
                        print(f"\n🛑 DEBUG: Достигнут лимит в 3 запроса. Программа завершается.")
                        break

                    # Извлекаем текст без номера
                    text_without_number = match.group(1)

                    print(f"\nОбработка строки {line_num}: {line}")
                    print(f"Текст без номера: {text_without_number}")

                    # Формируем полное сообщение для LLM
                    full_message = MESSAGE_PREFIX + text_without_number

                    try:
                        # Отправляем запрос к LLM
                        response = client.chat.completions.create(
                            model=MODEL,
                            messages=[
                                {"role": "user", "content": full_message}
                            ]
                        )

                        # Увеличиваем счетчик запросов
                        request_count += 1

                        # Получаем ответ
                        llm_response = response.choices[0].message.content

                        print(f"Получен ответ от LLM (первые 100 символов): {llm_response[:100]}...")
                        print(f"Обработано запросов: {request_count}")

                        # Записываем исходную строку и ответ LLM в выходной файл
                        output_file.write(f"Исходная строка: {line}\n")
                        output_file.write(f"Ответ LLM: {llm_response}\n")
                        output_file.write("-" * 80 + "\n\n")

                        # Задержка между запросами (не применяется после последнего запроса в DEBUG режиме)
                        if not (DEBUG and request_count >= 3):
                            print(f"⏳ Ожидание {DELAY_BETWEEN_REQUESTS} секунд перед следующим запросом...")
                            time.sleep(DELAY_BETWEEN_REQUESTS)

                    except Exception as e:
                        error_msg = f"Ошибка при обращении к LLM: {e}"
                        print(error_msg)
                        output_file.write(f"Исходная строка: {line}\n")
                        output_file.write(f"Ошибка: {error_msg}\n")
                        output_file.write("-" * 80 + "\n\n")
                else:
                    print(f"Строка {line_num} пропущена (не начинается с числа): {line[:50]}...")

        print(f"\n✅ Обработка завершена. Всего обработано запросов: {request_count}")
        print(f"Результаты записаны в {OUTPUT_FILE_PATH}")

    except FileNotFoundError:
        print(f"❌ Ошибка: Файл {INPUT_FILE_PATH} не найден!")
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")


if __name__ == "__main__":
    process_file()
