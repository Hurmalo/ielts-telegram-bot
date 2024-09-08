from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import os
import openai

# Define stages of the conversation
SELECTING_TASK, SELECTING_TOPIC, WRITING_ESSAY, PROVIDING_FEEDBACK = range(4)

# Initialize API keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("No TELEGRAM_TOKEN provided")
if not OPENAI_API_KEY:
    raise ValueError("No OPENAI_API_KEY provided")

openai.api_key = OPENAI_API_KEY

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        ["Practice Writing"],
        ["Practice Tenses"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Welcome to the IELTS Helper Bot! Choose a task:", reply_markup=reply_markup)
    return SELECTING_TASK

# Task selection handler
async def task_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_choice = update.message.text
    if user_choice == "Practice Writing":
        # Show available topics for essay writing
        keyboard = [[topic] for topic in ["Art", "Business", "Health", "Technology", "Tourism"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text("Select a topic for your essay:", reply_markup=reply_markup)
        return SELECTING_TOPIC
    elif user_choice == "Practice Tenses":
        await update.message.reply_text("Tense practice is not implemented yet.")
        return SELECTING_TASK

# Topic selection handler
async def topic_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    selected_topic = update.message.text
    context.user_data['selected_topic'] = selected_topic

    # Send instructions for the essay
    await update.message.reply_text(f"Great! You selected {selected_topic}. Please write an essay (minimum 250 words).")
    return WRITING_ESSAY

# Essay submission handler
async def essay_submission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_essay = update.message.text
    selected_topic = context.user_data['selected_topic']

    # Call OpenAI to analyze the essay
    response = openai.ChatCompletion.create(
    model="gpt-4o-mini",  # Updated model
    messages=[
        {"role": "system", "content": "You are an IELTS essay evaluator."},
        {"role": "user", "content": f"Analyze this essay:\n\n{user_essay}\n\nProvide feedback on grammar, vocabulary, structure, and coherence. Also point out any improvements."}
    ],
    max_tokens=200
)
    
    feedback = response.choices[0].text.strip()
    await update.message.reply_text(f"Feedback for your essay on {selected_topic}:\n\n{feedback}")

    return SELECTING_TASK

# Main function to set up the bot and handlers
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_selection)],
            SELECTING_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, topic_selection)],
            WRITING_ESSAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, essay_submission)],
        },
        fallbacks=[CommandHandler('start', start)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
