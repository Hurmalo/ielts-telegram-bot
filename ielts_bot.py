import os
import openai
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize API keys from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("Missing TELEGRAM_TOKEN or OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# Start the bot and provide basic commands and setup
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = "Welcome to the IELTS Preparation Bot! Choose a task to start:\n1. Writing Practice 📝\n2. Tense Practice ⏳"
    keyboard = [
        [KeyboardButton("📝 Writing Practice"), KeyboardButton("⏳ Tense Practice")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# Function to handle errors
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    await update.message.reply_text("Something went wrong. Please try again later.")

# Writing Practice: topic selection
async def writing_practice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    topics = [
        "Tourism", "Technology", "Education", "Health", "Environment", 
        "Family & Children", "Government", "Language", "Leisure", 
        "Media & Advertising", "Society", "Space Exploration", "Sport & Exercise", 
        "Transport", "Work", "Crime & Punishment", "Communication & Personality", 
        "Housing & Urban Planning", "Food & Diet", "Business & Money"
    ]
    
    keyboard = [[KeyboardButton(topic)] for topic in topics]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text("Please select a topic for writing practice:", reply_markup=reply_markup)

# Handle topic selection, generate essay instructions
async def handle_topic_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    selected_topic = update.message.text
    prompt = f"Generate 20 vocabulary words at a B1 level related to the topic '{selected_topic}'"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        vocabulary_words = response.choices[0].message['content'].strip()
        essay_instruction = f"Write an essay on the topic '{selected_topic}'. Use the following 20 words:\n{vocabulary_words}\n\nMinimum length: 250 words."
        
        await update.message.reply_text(essay_instruction)
    except openai.error.OpenAIError as e:
        await update.message.reply_text(f"Error fetching data from OpenAI: {str(e)}")

# Handle essay submission
async def submit_essay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    essay_text = update.message.text
    prompt = f"Check this IELTS essay for grammar, vocabulary, and structure:\n{essay_text}"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        feedback = response.choices[0].message['content'].strip()
        await update.message.reply_text(f"Feedback on your essay:\n{feedback}")
    except openai.error.OpenAIError as e:
        await update.message.reply_text(f"Error fetching data from OpenAI: {str(e)}")

# Tense Practice: Generates a fill-in-the-blanks task
async def tense_practice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prompt = "Generate a fill-in-the-blank exercise focusing on verb tenses."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        tense_task = response.choices[0].message['content'].strip()
        await update.message.reply_text(tense_task)
        await update.message.reply_text("Fill in the blanks with the correct verb forms and send your answers as a comma-separated list.")
    except openai.error.OpenAIError as e:
        await update.message.reply_text(f"Error fetching data from OpenAI: {str(e)}")

# Handle tense practice answers
async def check_tense_answers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_answers = update.message.text
    prompt = f"Check these answers for tense correctness:\n{user_answers}"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        feedback = response.choices[0].message['content'].strip()
        await update.message.reply_text(f"Feedback on your answers:\n{feedback}")
    except openai.error.OpenAIError as e:
        await update.message.reply_text(f"Error fetching data from OpenAI: {str(e)}")

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("📝 Writing Practice"), writing_practice))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("⏳ Tense Practice"), tense_practice))
    
    # Add message handlers for essay and tense task submission
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topic_selection))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, submit_essay))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_tense_answers))

    # Error handler
    application.add_error_handler(error_handler)

    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
