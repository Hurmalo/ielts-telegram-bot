import logging
import openai
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

# Access the API keys from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

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

    # Reset user data flags
    context.user_data['is_writing'] = False
    context.user_data['is_tense_practice'] = False

    # Keyboard with task options
    keyboard = [
        [InlineKeyboardButton("Practice Writing", callback_data='practice_writing')],
        [InlineKeyboardButton("Practice Tenses", callback_data='practice_tenses')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send welcome message with task options
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# Handle task selection (writing or tense practice)
async def task_selection(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    logger.info(f"User selected: {query.data}")

    if query.data == 'practice_writing':
        context.user_data['is_writing'] = True
        context.user_data['is_tense_practice'] = False
        await writing_task(query)
    elif query.data == 'practice_tenses':
        context.user_data['is_writing'] = False
        context.user_data['is_tense_practice'] = True
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

    # Save the selected topic to user data
    context.user_data["selected_topic"] = topic

    await query.answer()

    try:
        # Logging when starting vocabulary and question generation
        logger.info(f"Generating vocabulary and essay task for topic: {topic}")

        # Generate vocabulary and question for the selected topic
        vocab = await generate_vocabulary(topic)
        vocab_str = "\n".join(vocab)
        logger.info(f"Vocabulary generated for {topic}: {vocab}")

        question = await generate_essay_question(topic)
        logger.info(f"Essay question generated for {topic}: {question}")

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

        # Logging when instructions are successfully generated
        logger.info(f"Instructions generated for topic: {topic}")

        # Display instructions with useful vocabulary and question
        keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=instructions,
            reply_markup=reply_markup
        )

    except Exception as e:
        # Logging in case of an error
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

# Go back to the main menu
async def back_to_menu(update: Update, context: CallbackContext) -> None:
    logger.info("Returning to main menu")
    
    query = update.callback_query
    await query.answer()
    await start(update, context)

# Handle essay submission and provide feedback (including useful vocabulary check)
async def handle_essay_submission(update: Update, context: CallbackContext) -> None:
    essay_text = update.message.text
    selected_topic = context.user_data.get("selected_topic")

    # Check if the user is submitting an essay or tense practice answer
    if context.user_data.get('is_writing'):
        if not selected_topic:
            await update.message.reply_text("Please choose a topic before submitting your essay.")
            return

        logger.info(f"Received essay for topic: {selected_topic}")
        
        # Get feedback from OpenAI
        feedback = await get_essay_feedback(essay_text, selected_topic)
        await update.message.reply_text(feedback)
    elif context.user_data.get('is_tense_practice'):
        # Handle tense practice response
        await handle_tense_response(update, context)

# Handle tense practice response
async def handle_tense_response(update: Update, context: CallbackContext) -> None:
    answer = update.message.text
    logger.info(f"User provided tense practice answer: {answer}")
    
    # TODO: Add OpenAI check for tense practice answers

# Finalizing the bot by integrating all parts
def main():
    application = Application.builder().token(telegram_token).build()

    # Command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Callback query handler for task selection (writing or tense practice)
    application.add_handler(CallbackQueryHandler(task_selection))

    # Callback query handler for topic selection and vocabulary generation
    application.add_handler(CallbackQueryHandler(topic_chosen, pattern="topic_"))

    # Callback query handler for going back to main menu
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern="back_to_menu"))

    # Message handler for essay submission or tense response
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_essay_submission))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
