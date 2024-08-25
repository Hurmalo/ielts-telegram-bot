 import os
import random
import openai
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Установите ваши API ключи
openai.api_key = os.getenv("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")
telegram_token = os.getenv("7413264545:AAHjqKfNONUOxbWzI-D5YXqu2N59Kiqe_us")

# Список тем IELTS
topics = [
    "Art", "Business & Money", "Communication & Personality", "Crime & Punishment", "Education",
    "Environment", "Family & Children", "Food & Diet", "Government", "Health",
    "Housing, Buildings & Urban Planning", "Language", "Leisure", "Media & Advertising", "Reading",
    "Society", "Space Exploration", "Sport & Exercise", "Technology", "Tourism and Travel",
    "Transport", "Work"
]

# Приветственное сообщение и выбор задания
def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "Hello! I am your IELTS essay assistant bot. I can help you prepare for the writing part of the IELTS.\n\n"
        "Please choose a task:\n"
        "1. Select a topic for an essay\n"
        "2. Get a random topic 🎲\n"
        "3. Practice English tenses"
    )
    keyboard = [
        ["Select a topic for an essay"],
        ["🎲 Random topic"],
        ["Practice English tenses"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(welcome_message, reply_markup=reply_markup)

# Генерация списка тем с использованием OpenAI
def generate_topics():
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt="Generate 22 IELTS essay topics.",
        max_tokens=150
    )
    topics = response.choices[0].text.strip().split("\n")
    return topics[:22]

# Генерация слов по теме
def generate_words(topic):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Generate 10 academic-level words suitable for an IELTS essay on the topic '{topic}' for students aiming for a band score of 5.5 or higher.",
        max_tokens=50
    )
    words = response.choices[0].text.strip().split("\n")
    return words

# Обработка выбора темы
def handle_topic_selection(update: Update, context: CallbackContext) -> None:
    topics = generate_topics()
    keyboard = [[topic] for topic in topics]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text("Please choose a topic:", reply_markup=reply_markup)

# Обработка случайной темы
def handle_random_topic(update: Update, context: CallbackContext) -> None:
    topics = generate_topics()
    selected_topic = random.choice(topics)
    handle_topic_choice(update, context, selected_topic)

# Обработка выбранной темы и выдача слов
def handle_topic_choice(update: Update, context: CallbackContext, selected_topic):
    words = generate_words(selected_topic)
    word_list = "\n".join(f"- {word}" for word in words)
    response_message = (
        f"Write an essay on '{selected_topic}'. The minimum length is 250 words.\n\n"
        "Use the following words in the essay:\n" + word_list
    )
    context.user_data["selected_topic"] = selected_topic
    context.user_data["required_words"] = words
    update.message.reply_text(response_message)

# Проверка эссе и выдача обратной связи
def check_essay(essay_text, required_words):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=(
            f"Please review the following IELTS essay for grammar, style, and spelling errors. "
            f"Check if all required words are used and the essay length is appropriate.\n\n"
            f"Essay: {essay_text}\n\n"
            f"Required words: {', '.join(required_words)}"
        ),
        max_tokens=500
    )
    feedback = response.choices[0].text.strip()
    return feedback

def handle_essay_submission(update: Update, context: CallbackContext) -> None:
    essay_text = update.message.text
    required_words = context.user_data.get("required_words", [])
    feedback = check_essay(essay_text, required_words)
    provide_feedback(update, context, feedback, len(essay_text.split()), required_words)

# Предоставление обратной связи пользователю
def provide_feedback(update: Update, context: CallbackContext, feedback, word_count, required_words):
    missing_words = [word for word in required_words if word not in update.message.text]
    if word_count < 250:
        update.message.reply_text(f"Your essay contains less than 250 words. Word count: {word_count}")
    if missing_words:
        update.message.reply_text(f"The following words were not used: {', '.join(missing_words)}")
    update.message.reply_text(f"Here is your feedback:\n\n{feedback}")

# Практика времен английского языка: Выбор задания
def handle_tenses_practice(update: Update, context: CallbackContext) -> None:
    keyboard = [
        ["Convert sentences to another tense"],
        ["Fill in the blanks with the correct verb form"],
        ["Create a sentence using a given tense"],
        ["Choose the correct tense in context"],
        ["Practice tenses in dialogues"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text("Please choose a tenses practice task:", reply_markup=reply_markup)

# Обработка упражнений по временам английского языка
def handle_tense_task_selection(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    if user_message == "Convert sentences to another tense":
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt="Give a sentence and ask to convert it to another tense.",
            max_tokens=50
        )
        task = response.choices[0].text.strip()
        update.message.reply_text(f"Task: {task}")
    elif user_message == "Fill in the blanks with the correct verb form":
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt="Create a sentence with a missing verb and ask to fill it in with the correct tense.",
            max_tokens=50
        )
        task = response.choices[0].text.strip()
        update.message.reply_text(f"Task: {task}")
    elif user_message == "Create a sentence using a given tense":
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt="Ask the user to create a sentence using the present perfect tense.",
            max_tokens=50
        )
        task = response.choices[0].text.strip()
        update.message.reply_text(f"Task: {task}")
    elif user_message == "Choose the correct tense in context":
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt="Provide a sentence with multiple tense options and ask to choose the correct one.",
            max_tokens=50
        )
        task = response.choices[0].text.strip()
        update.message.reply_text(f"Task: {task}")
    elif user_message == "Practice tenses in dialogues":
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt="Create a short dialogue with missing tenses and ask the user to complete it.",
            max_tokens=50
        )
        task = response.choices[0].text.strip()
        update.message.reply_text(f"Task: {task}")
    else:
        update.message.reply_text("Please choose one of the provided options.")

# Обработка всех текстовых сообщений
def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    if user_message == "Select a topic for an essay":
        handle_topic_selection(update, context)
    elif user_message == "🎲 Random topic":
        handle_random_topic(update, context)
    elif user_message == "Practice English tenses":
        handle_tenses_practice(update, context)
    elif user_message in ["Convert sentences to another tense", "Fill in the blanks with the correct verb form",
                          "Create a sentence using a given tense", "Choose the correct tense in context",
                          "Practice tenses in dialogues"]:
        handle_tense_task_selection(update, context)
    elif context.user_data.get("selected_topic"):
        handle_essay_submission(update, context)
    else:
        update.message.reply_text("Please choose one of the provided options.")

# Основная функция для запуска бота
def main() -> None:
    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
