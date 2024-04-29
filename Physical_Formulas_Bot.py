import logging
from telegram.ext import Application, CommandHandler
from telegram import Update
import random
import os
import asyncio
import matplotlib.pyplot as plt
from telegram.ext import InlineQueryHandler  # Импорт обработчика инлайн-запросов
from telegram import InlineQueryResultArticle, InputTextMessageContent  # Импорт типов результатов инлайн-запроса
from uuid import uuid4  # Импорт функции для генерации уникальных идентификаторов


# Настройка логгирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Путь к файлу с токеном
token_file = 'my_token.txt'

# Токен моего бота
with open(token_file, 'r') as file:
    token = file.read().strip()  # Читаем содержимое файла и удаляем лишние пробелы и переносы строк

 # Директория для временных файлов
TEMP_DIR = "temp"

# Загрузка формул из файла
def load_formulas(filename):
    """
    Функция для загрузки формул из файла.

    Args:
        filename (str): Имя файла с формулами.

    Returns:
        dict: Словарь формул, где ключи - разделы, значения - список кортежей (название, формула, описание).
    """
    formulas = {}
    current_section = ""
    formula_name = ""
    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line.startswith("@@@"):
                current_section = line[3:].strip()
                formulas[current_section] = []
            elif line.startswith("###"):
                formula_name = line[3:].strip()
            elif line:
                formula, description = line.split("|||")
                formulas[current_section].append((formula_name, formula.strip(), description.strip()))
    return formulas

# Словарь всех формул
all_formulas = load_formulas("formulas.txt")

# Команды для базового управления
async def start(update: Update, context):
    """
    Команда /start. Начало работы с ботом.
    """
    await update.message.reply_text("Привет! Я бот формул физики. Используй /help для списка команд.")

async def help_command(update: Update, context):
    """
    Команда /help. Выводит список доступных команд.
    """
    help_text = """
    Доступные команды:
    /start - начать работу
    /help - помощь
    /search название формулы - поиск формулы по названию
    /random - случайная формула
    /add_section <name> - добавить раздел
    /add_formula <section> <name> <formula> <description> - добавить формулу
    /delete_section <name> - удалить раздел
    /delete_formula <section> <name> - удалить формулу из раздела
    /all - названия всех разделов и формул в них
    /save - сохранить изменения
    /formula_help <название формулы> - получить дополнительную информацию о формуле
    """
    await update.message.reply_text(help_text)

async def random_formula(update: Update, context):
    """
    Команда /random. Выводит случайную формулу из всех разделов.
    """
    section = random.choice(list(all_formulas.keys()))
    formula_name, formula, description = random.choice(all_formulas[section])
    await send_formula(update, section, formula_name, formula, description)

async def search_formula(update: Update, context):
    """
    Команда /search <название формулы>. Ищет формулу по названию.
    """
    query = " ".join(context.args).strip().lower()
    found_formulas = []
    for section, formulas in all_formulas.items():
        for name, formula, description in formulas:
            if query in name.lower():
                found_formulas.append((section, name, formula, description))
    if found_formulas:
        for section, name, formula, description in found_formulas:
            await send_formula(update, section, name, formula, description)
    else:
        await update.message.reply_text("Формула не найдена.")

async def add_section(update: Update, context):
    """
    Команда /add_section <название раздела>. Добавляет новый раздел.
    """
    section_name = " ".join(context.args).strip()
    if section_name and section_name not in all_formulas:
        all_formulas[section_name] = []
        await update.message.reply_text(f"Раздел '{section_name}' добавлен.")
    else:
        await update.message.reply_text("Укажите название раздела или такой раздел уже существует.")

async def add_formula(update: Update, context):
    """
    Команда /add_formula <раздел> <название> <формула> <описание>. Добавляет новую формулу в указанный раздел.
    """
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("Недостаточно аргументов. Используйте формат /add_formula <раздел> <название> <формула> <описание>")
        return
    section = args[0]
    if section in all_formulas:
        name = args[1]
        formula = args[2]
        description = " ".join(args[3:])
        all_formulas[section].append((name, formula, description))
        await update.message.reply_text(f"Формула '{name}' добавлена в раздел '{section}'.")
    else:
        await update.message.reply_text("Раздел не найден. Добавьте раздел командой /add_section.")

def save_formulas(formulas, filename):
    """
    Сохраняет формулы в файл.

    Args:
        formulas (dict): Словарь формул.
        filename (str): Имя файла для сохранения.
    """
    with open(filename, "w", encoding="utf-8") as file:
        for section, section_formulas in formulas.items():
            file.write(f"@@@{section}:\n")
            for name, formula, description in section_formulas:
                file.write(f"### {name}\n")
                file.write(f"{formula}|||{description}\n")

def all_sections_and_formulas():
    """
    Возвращает строку со списком всех разделов и формул в них.

    Returns:
        str: Список разделов и формул.
    """
    result = ""
    for section, section_formulas in all_formulas.items():
        result += f"{section}:\n"
        for name, _, _ in section_formulas:
            result += f"- {name}\n"
    return result

async def all_sections_and_formulas_command(update: Update, context):
    """
    Команда /all. Выводит названия всех разделов и формул в них.
    """
    message = all_sections_and_formulas()
    await update.message.reply_text(message)

async def save(update: Update, context):
    """
    Команда /save. Сохраняет изменения в формулах.
    """
    save_formulas(all_formulas, "formulas.txt")
    await update.message.reply_text("Формулы сохранены.")

# Функция для отправки формулы в чат
async def send_formula(update: Update, section: str, name: str, formula: str, description: str):
    """
    Отправляет формулу в чат.

    Args:
        update (Update): Объект обновления сообщения.
        section (str): Название раздела.
        name (str): Название формулы.
        formula (str): Текст формулы.
        description (str): Описание формулы.
    """
    await update.message.reply_text(f"Раздел Физики - {section}\nНазвание формулы - {name}:\n{formula} - {description}")

    # Генерация изображения формулы LaTeX
    fig, ax = plt.subplots()
    ax.text(0.5, 0.5, f"${formula}$", size=50, ha='center')
    ax.axis('off')

    # Сохранение изображения во временном файле
    image_path = os.path.join(TEMP_DIR, f"{name}.png")
    plt.savefig(image_path, bbox_inches='tight', pad_inches=0)
    plt.close()

    # Отправка изображения в чат
    with open(image_path, "rb") as photo:
        await update.message.reply_photo(photo)

    # Удаление временного файла PNG
    os.remove(image_path)

async def delete_section(update: Update, context):
    """
    Команда /delete_section <название раздела>. Удаляет указанный раздел.
    """
    section_name = " ".join(context.args).strip()
    if section_name in all_formulas:
        del all_formulas[section_name]
        await update.message.reply_text(f"Раздел '{section_name}' удален.")
    else:
        await update.message.reply_text("Указанный раздел не существует.")

async def delete_formula(update: Update, context):
    """
    Команда /delete_formula <раздел> <название>. Удаляет указанную формулу из указанного раздела.
    """
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Недостаточно аргументов. Используйте формат /delete_formula <раздел> <название>")
        return
    section = args[0]
    name = args[1]
    if section in all_formulas:
        formulas_in_section = all_formulas[section]
        for formula in formulas_in_section:
            if formula[0].lower() == name.lower():
                formulas_in_section.remove(formula)
                await update.message.reply_text(f"Формула '{name}' удалена из раздела '{section}'.")
                return
        await update.message.reply_text("Указанная формула не найдена в указанном разделе.")
    else:
        await update.message.reply_text("Указанный раздел не существует.")

async def formula_help(update: Update, context):
    """
    Команда /formula_help <название формулы>. Выводит дополнительную информацию о конкретной формуле.
    """
    query = " ".join(context.args).strip().lower()
    found_formula = None
    for section, formulas in all_formulas.items():
        for name, formula, description in formulas:
            if query in name.lower():
                found_formula = (section, name, formula, description)
                break
        if found_formula:
            break
    if found_formula:
        section, name, formula, description = found_formula
        await send_formula(update, section, name, formula, description)
    else:
        await update.message.reply_text("Формула не найдена.")

async def inline_query(update: Update, context):
    """Обработчик inline-запросов."""
    query = update.inline_query.query.strip().lower()  # Получаем текст запроса пользователя и приводим его к нижнему регистру
    results = []  # Инициализация списка для хранения результатов

    # Поиск формул по запросу
    for section, formulas in all_formulas.items():  # Перебираем все разделы и формулы
        for name, formula, description in formulas:  # Перебираем названия, формулы и описания внутри каждого раздела
            if query in name.lower() or query in description.lower():  # Проверяем, содержит ли название или описание запрос пользователя
                # Формируем текст результата для отображения
                result_content = f"Раздел: {section}\nНазвание: {name}\n{formula}\nОписание: {description}"
                # Создаем результат инлайн-запроса типа "Статья" (текстовый результат)
                results.append(
                    InlineQueryResultArticle(
                        id=uuid4(),  # Генерируем уникальный идентификатор для результата
                        title=name,  # Заголовок результата (название формулы)
                        description=f"Раздел: {section}",  # Описание результата (название раздела)
                        input_message_content=InputTextMessageContent(result_content)  # Текст сообщения результата
                    )
                )

    # Отправка результатов в чат
    await update.inline_query.answer(results, cache_time=0)
    # Отправляем результаты в ответ на запрос пользователя с отключенным кэшированием

if __name__ == "__main__":

    # Создаем асинхронную очередь для обновлений
    update_queue = asyncio.Queue()

    # Создаем объект приложения
    app = Application.builder().token(token).update_queue(update_queue).build()

    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("random", random_formula))
    app.add_handler(CommandHandler("search", search_formula))
    app.add_handler(CommandHandler("add_section", add_section))
    app.add_handler(CommandHandler("add_formula", add_formula))
    app.add_handler(CommandHandler("all", all_sections_and_formulas_command))
    app.add_handler(CommandHandler("save", save))
    app.add_handler(CommandHandler("delete_section", delete_section))
    app.add_handler(CommandHandler("delete_formula", delete_formula))
    app.add_handler(CommandHandler("formula_help", formula_help))

    # Регистрация обработчика инлайн-запросов в приложении
    app.add_handler(InlineQueryHandler(inline_query))
    """
    Инлайн-режим в Telegram позволяет пользователям отправлять запросы напрямую из чата, 
    используя символ "@" и имя бота, а затем вводить текст запроса. Бот может отвечать 
    на эти запросы непосредственно в том же чате, предоставляя текстовые или визуальные 
    результаты. Обработчик инлайн-запросов позволяет боту обрабатывать эти запросы и 
    отправлять соответствующие результаты.
    """

    # Запускаем приложение
    app.run_polling()
