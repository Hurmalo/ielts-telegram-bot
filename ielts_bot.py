import logging
import os  # Add this line to import the os module
import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

# Set your OpenAI API key and Telegram bot token using environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")  # Ensure you have set the environment variable for OPENAI_API_KEY
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")  # Ensure you have set the environment variable for TELEGRAM_BOT_TOKEN

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Greet the user with a welcome message and present task options
async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "Hello, welcome to the IELTS Preparation Bot! 🎓\n\n"
        "I am here to help you practice your writing skills for the IELTS exam and improve your use of English tenses. "
        "You can choose between two tasks:\n\n"
        "1️⃣ Practice Writing: I'll give you a writing topic with useful vocabulary words to help you.\n"
        "2️⃣ Practice Tenses: I'll test your knowledge of English tenses with interactive exercises.\n"
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

# Writing task: Display IELTS topics and add back button
async def writing_task(query) -> None:
    logger.info("Displaying writing topics")
    
    topics = [
        "Art", "Business & Money", "Communication & Personality", "Crime & Punishment", "Education",
        "Environment", "Family & Children", "Food & Diet", "Government", "Health", "Housing",
        "Language", "Leisure", "Media & Advertising", "Reading", "Society", "Space Exploration",
        "Sport & Exercise", "Technology", "Tourism", "Transport", "Work"
    ]

    keyboard = [[InlineKeyboardButton(topic, callback_data=f"topic_{topic}")] for topic in topics]
    keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data='back_to_menu')])  # Back button
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Please choose an IELTS writing topic:", reply_markup=reply_markup)

# Handle topic selection and provide essay instructions, vocabulary, and a question
async def topic_chosen(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    topic = query.data.split("_")[1]  # Extract topic from callback data

    logger.info(f"Topic selected: {topic}")

    try:
        # Generate vocabulary and question for the selected topic
        vocab = await generate_vocabulary(topic)
        vocab_str = "\n".join(vocab)

        question = await generate_essay_question(topic)

        instructions = (
            f"Topic: {topic}\n\n"
            f"Essay Task: {question}\n"
            f"Word Count: Minimum 250 words\n"
            f"Useful Vocabulary:\n{vocab_str}\n\n"
            "How to Write an IELTS Essay:\n"
            "1. Introduction: Clearly state your position on the topic.\n"
            "2. Body Paragraphs: Use 2-3 paragraphs to support your opinion.\n"
            "3. Conclusion: Summarize your argument.\n"
            "Once you're done, submit your essay here."
        )

        keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error generating vocabulary or essay question for topic {topic}: {e}")
        await query.edit_message_text("Sorry, there was an error generating the task. Please try again later.")

# Generate vocabulary based on the selected topic using OpenAI
async def generate_vocabulary(topic: str) -> list:
    logger.info(f"Generating vocabulary for topic: {topic}")
    
    try:
        prompt = f"Generate 10 advanced vocabulary words related to the IELTS topic '{topic}'."
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=50,
            n=1,
            temperature=0.5
        )
        vocabulary = response.choices[0].text.strip().split("\n")
        return vocabulary
    except Exception as e:
        logger.error(f"Error generating vocabulary for topic {topic}: {e}")
        raise e

# Generate a specific IELTS-style question based on the selected topic
async def generate_essay_question(topic: str) -> str:
    logger.info(f"Generating essay question for topic: {topic}")
    
    try:
        prompt = f"Generate an IELTS writing task related to the topic '{topic}'."
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=100,
            n=1,
            temperature=0.7
        )
        question = response.choices[0].text.strip()
        return question
    except Exception as e:
        logger.error(f"Error generating essay question for topic {topic}: {e}")
        raise e

# Handle tense task selection
async def tense_task(query) -> None:
    logger.info("Generating tense practice task")

    # Example tense practice
    tense_question = (
        "Tense: Future Continuous\n"
        "Complete the sentence: At this time tomorrow, we _____ (fly) to Japan.\n"
        "Time marker: At this time tomorrow"
    )

    instructions = (
        f"{tense_question}\n\n"
        "Use the verb in the correct tense form based on the time marker."
    )

    keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=instructions, reply_markup=reply_markup)

# Handle essay submission: Accept essay text and provide feedback using OpenAI
async def handle_essay_submission(update: Update, context: CallbackContext) -> None:
    user_essay = update.message.text
    logger.info(f"Received essay submission: {user_essay}")

    # Send the essay to OpenAI for grammar, style, and spelling correction
    try:
        prompt = (
            f"Provide feedback and corrections for the following IELTS essay:\n\n"
            f"{user_essay}\n\n"
            "Correct any grammar, spelling, and style mistakes, and provide a summary of the feedback."
        )

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=300,
            temperature=0.6
        )

        feedback = response.choices[0].text.strip()

        await update.message.reply_text(
            f"Here is the feedback on your essay:\n\n{feedback}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error processing essay submission: {e}")
        await update.message.reply_text("Sorry, there was an error processing your essay. Please try again later.")

# Finalizing the bot by integrating all parts
def main():
    application = Application.builder().token(telegram_token).build()

    # Command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Callback query handler for task selection (writing or tense practice)
    application.add_handler(CallbackQueryHandler(task_selection))

    # Callback query handler for topic selection
    application.add_handler(CallbackQueryHandler(topic_chosen, pattern="topic_"))

    # Callback query handler for going back to main menu
    application.add_handler(CallbackQueryHandler(start, pattern="back_to_menu"))

    # Message handler for essay submission
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_essay_submission))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
