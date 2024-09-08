import logging
import os
import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# Set up the OpenAI API key and Telegram bot token
openai.api_key = os.getenv("OPENAI_API_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

# Set up logging for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Greet the user with a welcome message and present task options
async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "Hello, welcome to the IELTS Preparation Bot! 🎓\n\n"
        "Choose between:\n"
        "1️⃣ Practice Writing: I'll give you a writing topic with useful vocabulary.\n"
        "2️⃣ Practice Tenses: Test your knowledge of English tenses."
    )
    
    keyboard = [
        [InlineKeyboardButton("Practice Writing", callback_data='practice_writing')],
        [InlineKeyboardButton("Practice Tenses", callback_data='practice_tenses')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# Handle task selection (writing or tense practice)
async def task_selection(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    logger.info(f"User selected: {query.data}")

    if query.data == 'practice_writing':
        await writing_task(query)
    elif query.data == 'practice_tenses':
        await tense_task(query)

# Writing task: Display IELTS topics
async def writing_task(query) -> None:
    logger.info("Displaying writing topics")
    
    topics = [
        "Art", "Business & Money", "Communication & Personality", "Crime & Punishment", "Education",
        "Environment", "Family & Children", "Food & Diet", "Government", "Health", "Housing",
        "Language", "Leisure", "Media & Advertising", "Reading", "Society", "Space Exploration",
        "Sport & Exercise", "Technology", "Tourism", "Transport", "Work"
    ]
    
    keyboard = [[InlineKeyboardButton(topic, callback_data=f"topic_{topic}")] for topic in topics]
    keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data='back_to_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("Please choose an IELTS writing topic:", reply_markup=reply_markup)

# Handle topic selection
async def topic_chosen(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    topic = query.data.split("_")[1]  # Extract topic from callback data

    logger.info(f"User selected topic: {topic}")
    
    try:
        # Call OpenAI API to generate vocabulary and essay question
        logger.info("Calling OpenAI API for vocabulary and essay question generation...")
        vocab = await generate_vocabulary(topic)
        vocab_str = "\n".join(vocab)

        question = await generate_essay_question(topic)

        logger.info(f"Received response from OpenAI. Vocabulary: {vocab}, Question: {question}")

        instructions = (
            f"Topic: {topic}\n\n"
            f"Essay Task: {question}\n"
            f"Word Count: Minimum 250 words\n"
            f"Useful Vocabulary:\n{vocab_str}\n\n"
            "Follow this structure:\n"
            "1. Introduction\n"
            "2. Body Paragraphs\n"
            "3. Conclusion\n"
            "Submit your essay here when ready."
        )
        
        keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(instructions, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error generating essay task for {topic}: {e}")
        await query.edit_message_text("Error occurred while generating the task. Please try again later.")

# Generate vocabulary using OpenAI
async def generate_vocabulary(topic: str) -> list:
    logger.info(f"Generating vocabulary for topic: {topic}")
    
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Generate 10 vocabulary words related to the IELTS topic '{topic}'.",
            max_tokens=50,
            temperature=0.5
        )
        vocabulary = response.choices[0].text.strip().split("\n")
        return vocabulary
    except Exception as e:
        logger.error(f"Error generating vocabulary for topic {topic}: {e}")
        return ["Error generating vocabulary"]

# Generate essay question using OpenAI
async def generate_essay_question(topic: str) -> str:
    logger.info(f"Generating essay question for topic: {topic}")
    
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Generate an IELTS essay question based on the topic '{topic}'.",
            max_tokens=100,
            temperature=0.7
        )
        question = response.choices[0].text.strip()
        return question
    except Exception as e:
        logger.error(f"Error generating essay question for topic {topic}: {e}")
        return "Error generating essay question."

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
