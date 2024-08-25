import os
import random
import openai
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Установите ваши API ключи
openai.api_key = "sk-sNBKzFK1pWW4skvq4CtIAbJOb_SKfEN3_7LZ0WTN8VT3BlbkFJr86mM7dK_zDvILQVVMirppcqtXl7yGxv7NeRlEHxIA"
telegram_token = "7413264545:AAHjqKfNONUOxbWzI-D5YXqu2N59Kiqe_us"

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

# Обновленная функция генерации списка тем с использованием OpenAI
def generate_topics():
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Generate 22 IELTS essay topics."},
            {"role": "user", "content": "Please generate 22 IELTS essay topics."}
        ]
    )
    topics = response.choices[0].message['content'].strip().split("\n")
    return topics[:22]

# Обновленная функция генерации слов по теме
def generate_words(topic):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"Generate 10 academic-level words suitable for an IELTS essay on the topic '{topic}' for students aiming for a band score of 5.5 or higher."},
            {"role": "user", "content": f"Please generate 10 words for the topic '{topic}'."}
        ]
    )
    words = response.choices[0].message['content'].strip().split("\n")
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
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Please review the following IELTS essay for grammar, style, and spelling errors. "
                                          "Check if all required words are used and the essay length is appropriate."},
            {"role": "user", "content": f"Essay: {essay_text}\n\nRequired words: {', '.join(required_words)}"}
        ]
    )
    feedback = response.choices[0].message['content'].strip()
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
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Give a sentence and ask to convert it to another tense."},
                {"role": "user", "content": "Please provide a sentence to be converted to another tense."}
            ]
        )
        task = response.choices[0].message['content'].strip()
        update.message.reply_text(f"Task: {task}")
    elif user_message == "Fill in the blanks with the correct verb form":
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Create a sentence with a missing verb and ask to fill it in with the correct tense."},
                {"role": "user", "content": "Please create a fill-in-the-blank sentence."}
            ]
        )
        task = response.choices[0].message['content'].strip()
        update.message.reply_text(f"Task: {task}")
    elif user_message == "Create a sentence using a given tense":
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ask the user to create a sentence using the present perfect tense."},
                {"role": "user", "content": "Please create a sentence using the present perfect tense."}
            ]
        )
        task = response.choices[0].message['content'].strip()
        update.message.reply_text(f"Task: {task}")
    elif user_message == "Choose the correct tense in context":
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Provide a sentence with multiple tense options and ask to choose the correct one."},
                {"role": "user", "content": "Please provide a sentence with multiple tense options."}
            ]
        )
        task = response.choices[0].message['content'].strip()
        update.message.reply_text(f"Task: {task}")
    elif user_message == "Practice tenses in dialogues":
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Create a short dialogue with missing tenses and ask the user to complete it."},
                {"role": "user", "content": "Please create a short dialogue with missing tenses."}
            ]
        )
        task = response.choices[0].message['content'].strip()
        update.message.reply_text(f"Task: {task}")
    else:
        update.message.reply_text("Please choose one of the provided options.")

# Обработка всех текстовых сообщений
def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    
    # Обработка выбора темы для эссе
    if user_message == "Select a topic for an essay":
        handle_topic_selection(update, context)
    
    # Обработка случайной темы для эссе
    elif user_message == "🎲 Random topic":
        handle_random_topic(update, context)
    
    # Обработка выбора задания на проработку времен
    elif user_message == "Practice English tenses":
        handle_tenses_practice(update, context)
    
    # Обработка выполнения задания по временам
    elif user_message in [
        "Convert sentences to another tense", 
        "Fill in the blanks with the correct verb form",
        "Create a sentence using a given tense", 
        "Choose the correct tense in context",
        "Practice tenses in dialogues"
    ]:
        handle_tense_task_selection(update, context)
    
    # Обработка отправки эссе
    elif context.user_data.get("selected_topic"):
        handle_essay_submission(update, context)
    
    # Обработка неизвестных команд
    else:
        update.message.reply_text("Please choose one of the provided options.")

# Основная функция для запуска бота
def main() -> None:
    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    # Обработчик команды /start
    dispatcher.add_handler(CommandHandler("start", start))
    
    # Обработчик текстовых сообщений
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
