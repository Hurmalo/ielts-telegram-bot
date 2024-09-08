import logging
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Define your API keys (assumed as environment variables)
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# List of writing topics
writing_topics = [
    "Art", "Business & Money", "Communication & Personality", "Crime & Punishment",
    "Education", "Environment", "Family & Children", "Food & Diet", "Government", "Health",
    "Housing, Buildings & Urban Planning", "Language", "Leisure", "Media & Advertising",
    "Reading", "Society", "Space Exploration", "Sport & Exercise", "Technology", "Tourism and Travel", 
    "Transport", "Work"
]

# Function to handle the /start command
async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("Practice Writing", callback_data="practice_writing")],
        [InlineKeyboardButton("Practice Tenses", callback_data="practice_tenses")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose an option:", reply_markup=reply_markup)

# Function to handle task selection (writing or tenses)
async def task_selection(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "practice_writing":
        logger.info("User selected: practice_writing")
        await display_writing_topics(query)
    elif query.data == "practice_tenses":
        logger.info("User selected: practice_tenses")
        await generate_tense_task(query)

# Function to display writing topics
async def display_writing_topics(query):
    keyboard = [[InlineKeyboardButton(topic, callback_data=f"topic_{topic}")] for topic in writing_topics]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Please choose a writing topic:", reply_markup=reply_markup)

# Function to handle chosen writing topic
async def topic_chosen(update: Update, context):
    query = update.callback_query
    await query.answer()

    topic = query.data.split("_")[1]
    logger.info(f"User selected: {topic}")

    # Generate essay instructions using OpenAI
    essay_instructions = await generate_essay_instructions(topic)

    # Send essay instructions
    await query.edit_message_text(f"Write an essay on the topic: {topic}\n\n"
                                  f"Instructions: {essay_instructions}")

# Function to generate essay instructions using OpenAI
async def generate_essay_instructions(topic):
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"Provide instructions for writing an essay on the topic {topic} suitable for IELTS preparation.",
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except Exception as e:
        logger.error(f"Error generating essay instructions: {e}")
        return "Sorry, I couldn't generate the instructions."

# Tense practice task
async def tense_task(query) -> None:
    logger.info("Generating tense practice task")

    tense_question = (
        "Tense: Future Continuous\n"
        "Complete the sentence: At this time tomorrow, we _____ (fly) to Japan."
    )
    
    keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(tense_question, reply_markup=reply_markup)

# Main function to set up handlers and run the bot
def main():
    application = Application.builder().token(telegram_token).build()

    # Command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Callback query handler for task selection
    application.add_handler(CallbackQueryHandler(task_selection))

    # Callback query handler for topic selection
    application.add_handler(CallbackQueryHandler(topic_chosen, pattern="topic_"))

    # Callback query handler for back to menu
    application.add_handler(CallbackQueryHandler(start, pattern="back_to_menu"))

    # Run the bot using polling
    application.run_polling()

if __name__ == '__main__':
    main()
