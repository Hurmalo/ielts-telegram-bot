import logging
import openai
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
from datetime import time

# Set up your API keys
openai.api_key = "OPENAI_API_KEY"
telegram_token = "TELEGRAM_BOT_TOKEN"

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Greet the user and present task options
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Practice Writing", callback_data='practice_writing')],
        [InlineKeyboardButton("Practice Tenses", callback_data='practice_tenses')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Welcome to the IELTS Preparation Bot! Select a task below:",
        reply_markup=reply_markup
    )

# Handle task selection (writing or tense practice)
async def task_selection(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'practice_writing':
        await writing_task(query)
    elif query.data == 'practice_tenses':
        await tense_task(query)

# Writing task: Display IELTS topics
async def writing_task(query) -> None:
    topics = [
        "Art", "Business & Money", "Communication & Personality", "Crime & Punishment", "Education",
        "Environment", "Family & Children", "Food & Diet", "Government", "Health", "Housing",
        "Language", "Leisure", "Media & Advertising", "Reading", "Society", "Space Exploration",
        "Sport & Exercise", "Technology", "Tourism", "Transport", "Work"
    ]

    keyboard = [[InlineKeyboardButton(topic, callback_data=f"topic_{topic}")] for topic in topics]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Please choose an IELTS writing topic:", reply_markup=reply_markup)

# Generate vocabulary based on the selected topic using OpenAI
async def generate_vocabulary(topic: str) -> list:
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

# Handle topic selection and provide vocabulary
async def topic_chosen(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    topic = query.data.split("_")[1]  # Extract topic from callback data

    await query.answer()

    vocab = await generate_vocabulary(topic)
    vocab_str = "\n".join(vocab)

    await query.edit_message_text(
        text=f"You selected the topic: {topic}\n\nHere are 10 words you can use in your essay:\n{vocab_str}"
    )

# Generate a tense practice question with time markers
async def tense_task(query) -> None:
    tense_prompts = [
        ("Present Simple", "He _____ (go) to the gym every day.", "Time marker: every day"),
        ("Past Continuous", "They _____ (watch) TV when the phone rang.", "Time marker: when the phone rang"),
        ("Future Perfect", "By next year, she _____ (complete) the course.", "Time marker: By next year"),
        # Add more tense examples here...
    ]

    tense, sentence, marker = random.choice(tense_prompts)

    await query.edit_message_text(
        f"Tense: {tense}\nComplete the sentence: {sentence}\n{marker}"
    )

# Handle essay submission and provide feedback
async def handle_essay_submission(update: Update, context: CallbackContext) -> None:
    essay_text = update.message.text
    user_data = context.user_data.get("selected_topic", "")

    if not user_data:
        await update.message.reply_text("Please choose a topic before submitting your essay.")
        return

    # Get feedback from OpenAI
    feedback = await get_essay_feedback(essay_text, user_data["topic"], user_data["vocabulary"])
    await update.message.reply_text(feedback)

# Get feedback using OpenAI
async def get_essay_feedback(essay: str, topic: str, vocabulary: list) -> str:
    prompt = (
        f"Analyze this essay for IELTS based on the topic '{topic}'. "
        f"Check for grammar, word count, and whether the following words are used: {', '.join(vocabulary)}. "
        "Provide feedback and suggestions for improvement."
    )
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=300,
        temperature=0.7
    )
    feedback = response.choices[0].text.strip()
    return feedback

# Set reminders for regular practice
async def set_reminder(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    try:
        reminder_time = time.fromisoformat(context.args[0])  # User provides time in HH:MM format
        context.job_queue.run_daily(reminder_message, reminder_time, context=chat_id)
        await update.message.reply_text(f"Reminder set for {reminder_time}. You will receive practice notifications daily.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /setreminder HH:MM")

# Send a reminder message
async def reminder_message(context: CallbackContext) -> None:
    job = context.job
    await context.bot.send_message(job.context, text="Don't forget to practice your IELTS today!")

# Handle /unsetreminder command to stop reminders
async def unset_reminder(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
    await update.message.reply_text("Reminders have been canceled.")

# Error handler
async def error(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning(f'Update {update} caused error {context.error}')

# Finalizing the bot by integrating all parts
def main():
    application = Application.builder().token(telegram_token).build()

    # Command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Command handler for setting reminders
    application.add_handler(CommandHandler("setreminder", set_reminder))

    # Command handler for unsetting reminders
    application.add_handler(CommandHandler("unsetreminder", unset_reminder))

    # Callback query handler for task selection (writing or tense practice)
    application.add_handler(CallbackQueryHandler(task_selection))

    # Callback query handler for topic selection and vocabulary generation
    application.add_handler(CallbackQueryHandler(topic_chosen, pattern="topic_"))

    # Message handler for essay submission (any non-command text)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_essay_submission))

    # Error handler
    application.add_error_handler(error)

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
