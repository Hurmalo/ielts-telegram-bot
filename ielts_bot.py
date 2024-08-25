import logging
import openai
import os
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Установите ваши API ключи
openai.api_key = os.getenv("OPENAI_API_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

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
    logging.info("Bot started by user")
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
    logging.info("Generating topics using OpenAI API")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Generate 22 IELTS essay topics."},
                {"role": "user", "content": "Please generate 22 IELTS essay topics."}
            ]
        )
        logging.info(f"OpenAI API response: {response}")
        topics = response.choices[0].message['content'].strip().split("\n")
        return topics[:22]
    except Exception as e:
        logging.error(f"Error in generate_topics: {e}")
        return []

# Обновленная функция генерации слов по теме
def generate_words(topic):
    logging.info(f"Generating words for topic: {topic}")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Generate 10 academic-level words suitable for an IELTS essay on the topic '{topic}' for students aiming for a band score of 5.5 or higher."},
                {"role": "user", "content": f"Please generate 10 words for the topic '{topic}'."}
            ]
        )
        logging.info(f"OpenAI API response for words: {response}")
        words = response.choices[0].message['content'].strip().split("\n")
        return words
    except Exception as e:
        logging.error(f"Error in generate_words: {e}")
        return []

# Обработка выбора темы
def handle_topic_selection(update: Update, context: CallbackContext) -> None:
    logging.info("User selected a topic")
    try:
        topics = generate_topics()
        logging.info(f"Generated topics: {topics}")
        if not topics:
            update.message.reply_text("No topics were generated.")
            return
        keyboard = [[topic] for topic in topics]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        update.message.reply_text("Please choose a topic:", reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error in handle_topic_selection: {e}")
        update.message.reply_text("An error occurred while generating topics.")

# Обработка случайной темы
def handle_random_topic(update: Update, context: CallbackContext) -> None:
    logging.info("User requested a random topic")
    try:
        topics = generate_topics()
        selected_topic = random.choice(topics)
        logging.info(f"Randomly selected topic: {selected_topic}")
        handle_topic_choice(update, context, selected_topic)
    except Exception as e:
        logging.error(f"Error in handle_random_topic: {e}")
        update.message.reply_text("An error occurred while selecting a random topic.")

# Обработка выбранной темы и выдача слов
def handle_topic_choice(update: Update, context: CallbackContext, selected_topic):
    logging.info(f"Handling selected topic: {selected_topic}")
    try:
        words = generate_words(selected_topic)
        logging.info(f"Generated words: {words}")
        word_list = "\n".join(f"- {word}" for word in words)
        response_message = (
            f"Write an essay on '{selected_topic}'. The minimum length is 250 words.\n\n"
            "Use the following words in the essay:\n" + word_list
        )
        context.user_data["selected_topic"] = selected_topic
        context.user_data["required_words"] = words
        update.message.reply_text(response_message)
    except Exception as e:
        logging.error(f"Error in handle_topic_choice: {e}")
        update.message.reply_text("An error occurred while generating words.")

# Проверка эссе и выдача обратной связи
def check_essay(essay_text, required_words):
    logging.info("Checking essay for errors and word usage")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Please review the following IELTS essay for grammar, style, and spelling errors. "
                                              "Check if all required words are used and the essay length is appropriate."},
                {"role": "user", "content": f"Essay: {essay_text}\n\nRequired words: {', '.join(required_words)}"}
            ]
        )
        feedback = response.choices[0].message['content'].strip()
        logging.info(f"Feedback received: {feedback}")
        return feedback
    except Exception as e:
        logging.error(f"Error in check_essay: {e}")
        return "An error occurred while checking the essay."

def handle_essay_submission(update: Update, context: CallbackContext) -> None:
    essay_text = update.message.text
    logging.info(f"Received essay text: {essay_text}")
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
    logging.info("User selected tenses practice")
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
    logging.info(f"User selected tense practice task: {user_message}")
    try:
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
            logging.warning(f"Unknown tense practice task: {user_message}")
            update.message.reply_text("Please choose one of the provided options.")
    except Exception as e:
        logging.error(f"Error in handle_tense_task_selection: {e}")
        update.message.reply_text("An error occurred while processing the tense practice task.")
        
# Обработка всех текстовых сообщений
def handle_message(update: Update, context: CallbackContext) -> None:
user_message = update.message.text
logging.info(f"Received message: {user_message}")
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
    logging.warning(f"Unknown command or message: {user_message}")
    update.message.reply_text("Please choose one of the provided options.")
def main() -> None:
application = Application.builder().token(telegram_token).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

application.run_polling()
if __name__ == '__main__':
main()
