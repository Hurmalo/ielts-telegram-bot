import os
import openai
import random
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# Set up your API keys
openai.api_key = "OPENAI_API_KEY"
telegram_token = "TELEGRAM_BOT_TOKEN"

# Define states for conversation handler
SELECTING_TASK, SELECTING_TOPIC, SUBMITTING_ESSAY, CHECKING_TENSES = range(4)

# List of possible topics
topics = []

# Start function to handle the /start command
def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "Hello! I am your IELTS essay assistant bot. I can help you prepare for the writing part of the IELTS.\n\n"
        "Please choose a task:\n"
        "1. Select a topic for an essay\n"
        "2. Get a random topic 🎲\n"
        "3. Practice English tenses"
    )
    keyboard = [
        [KeyboardButton("Select a topic for an essay")],
        [KeyboardButton("🎲 Random topic")],
        [KeyboardButton("Practice English tenses")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(welcome_message, reply_markup=reply_markup)
    return SELECTING_TASK

# Task selection handler
def select_task(update: Update, context: CallbackContext) -> int:
    user_choice = update.message.text

    if user_choice == "Select a topic for an essay":
        # Generate topics using OpenAI
        topics = generate_topics()
        keyboard = [[KeyboardButton(topic)] for topic in topics] + [[KeyboardButton("🎲 Random topic")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        update.message.reply_text("Please choose a topic:", reply_markup=reply_markup)
        return SELECTING_TOPIC

    elif user_choice == "🎲 Random topic":
        random_topic = random.choice(topics)
        context.user_data['selected_topic'] = random_topic
        return topic_selected(update, context)

    elif user_choice == "Practice English tenses":
        # Handle tenses practice task
        return practice_tenses(update, context)

    else:
        update.message.reply_text("Please choose a valid option.")
        return SELECTING_TASK

# Generate topics using OpenAI API
def generate_topics():
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt="Generate 22 IELTS essay topics.",
        max_tokens=150
    )
    topics = response.choices[0].text.strip().split("\n")
    return topics[:22]

# Handler for when a topic is selected
def topic_selected(update: Update, context: CallbackContext) -> int:
    selected_topic = update.message.text
    context.user_data['selected_topic'] = selected_topic
    instructions = f"Write an essay on '{selected_topic}'. The minimum length is 250 words."
    words = generate_words(selected_topic)
    word_list = "\n".join(f"- {word}" for word in words)
    response_message = f"{instructions}\n\nUse the following words in your essay:\n{word_list}"
    update.message.reply_text(response_message)
    return SUBMITTING_ESSAY

# Generate 10 words related to the selected topic
def generate_words(topic):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Generate 10 words to use in an essay on '{topic}'.",
        max_tokens=50
    )
    words = response.choices[0].text.strip().split("\n")
    return words

# Handler for practicing tenses
def practice_tenses(update: Update, context: CallbackContext) -> int:
    task_description = "Please use the following sentence and convert it into three different tenses."
    tenses_task = generate_tenses_task()
    update.message.reply_text(f"{task_description}\n\n{tenses_task}")
    return CHECKING_TENSES

# Generate a task for practicing tenses
def generate_tenses_task():
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt="Generate a sentence for practicing English tenses.",
        max_tokens=30
    )
    return response.choices[0].text.strip()

# Main function to run the bot
def main() -> None:
    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_TASK: [MessageHandler(Filters.text & ~Filters.command, select_task)],
            SELECTING_TOPIC: [MessageHandler(Filters.text & ~Filters.command, topic_selected)],
            SUBMITTING_ESSAY: [MessageHandler(Filters.text & ~Filters.command, lambda update, context: update.message.reply_text("Essay submission coming soon!"))],
            CHECKING_TENSES: [MessageHandler(Filters.text & ~Filters.command, lambda update, context: update.message.reply_text("Tenses checking coming soon!"))]
        },
        fallbacks=[CommandHandler('start', start)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
