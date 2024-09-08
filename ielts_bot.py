import os
import openai
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Load API keys from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY

# Conversation states
WRITING, TENSES, SUBMITTING_ESSAY = range(3)

# Writing topics
topics = [
    "Tourism", "Technology", "Education", "Health", "Environment", "Business", "Media", 
    "Government", "Family", "Society", "Crime & Punishment", "Communication & Personality",
    "Sport & Exercise", "Transport", "Work", "Art", "Language", "Housing", "Leisure", "Space Exploration"
]

# Function to generate OpenAI prompt for vocabulary words
def generate_vocabulary(topic):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an English language tutor helping a student prepare for IELTS."},
            {"role": "user", "content": f"Generate 20 vocabulary words for B1 level on the topic '{topic}'."}
        ]
    )
    return response.choices[0].message['content']

# Function to handle the start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        ["Writing Practice", "Practice Tenses"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text("Welcome to the IELTS bot! Please choose a task:", reply_markup=reply_markup)
    return WRITING

# Writing practice: topic selection
async def writing_practice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[topic] for topic in topics]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text("Please choose a topic for your essay:", reply_markup=reply_markup)
    return WRITING

# After topic selection, give essay instructions
async def topic_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    topic = update.message.text
    context.user_data['topic'] = topic

    # Generate vocabulary words for the selected topic using OpenAI
    vocabulary = generate_vocabulary(topic)

    await update.message.reply_text(f"Write an essay on the topic '{topic}'. Use the following words:\n{vocabulary}")
    await update.message.reply_text("The minimum length is 250 words. Submit your essay when ready.")

    return SUBMITTING_ESSAY

# Handle essay submission
async def submit_essay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    essay = update.message.text

    # Send the essay to OpenAI for feedback
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an IELTS essay grader."},
            {"role": "user", "content": f"Please provide feedback on this IELTS essay:\n{essay}"}
        ]
    )
    feedback = response.choices[0].message['content']

    # Send feedback to the user
    await update.message.reply_text(f"Thank you for submitting your essay! Here's your feedback:\n{feedback}")
    
    # Return to the main menu after essay feedback
    return await start(update, context)

# Tense practice function
async def practice_tenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['task'] = 'tenses'
    
    # Generate tense exercise using OpenAI
    tense_text = generate_tense_exercise()

    await update.message.reply_text(f"Fill in the blanks with the correct verb forms and send your answers as a comma-separated list:\n\n{tense_text}")

    return TENSES

# Generate tense exercise using OpenAI
def generate_tense_exercise():
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an English grammar tutor."},
            {"role": "user", "content": "Generate a tense exercise with blanks for students to fill in the correct verb forms."}
        ]
    )
    return response.choices[0].message['content']

# Handle tense answers
async def submit_tense_answers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answers = update.message.text

    # Send tense answers to OpenAI for correction
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an English grammar tutor."},
            {"role": "user", "content": f"Correct these tense answers:\n{answers}"}
        ]
    )
    feedback = response.choices[0].message['content']

    # Provide feedback on the tense exercise
    await update.message.reply_text(f"Here is your feedback on the tense exercise:\n{feedback}")

    # Return to the main menu after feedback
    return await start(update, context)

# Main function
def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Conversation handler for writing practice
    writing_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WRITING: [
                MessageHandler(filters.Regex("^(Writing Practice)$"), writing_practice),
                MessageHandler(filters.TEXT & ~filters.COMMAND, topic_selected),
            ],
            SUBMITTING_ESSAY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, submit_essay),
            ]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Conversation handler for tense practice
    tense_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(Practice Tenses)$"), practice_tenses)],
        states={
            TENSES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, submit_tense_answers),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(writing_conv_handler)
    application.add_handler(tense_conv_handler)

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
