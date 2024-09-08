import os
import openai
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import logging

# API Keys from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Conversation states
WRITING, TENSES, ESSAY_SUBMISSION = range(3)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [KeyboardButton("Writing Practice"), KeyboardButton("Practice Tenses")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    await update.message.reply_text(
        "Welcome to the IELTS Helper Bot! You can either practice writing or tenses. Please choose one:",
        reply_markup=reply_markup
    )
    
    return WRITING

# Writing Practice: topic selection
async def writing_practice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    topics = ["Tourism", "Technology", "Education", "Health", "Environment"]
    keyboard = [[KeyboardButton(topic)] for topic in topics]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text("Select a topic for your writing:", reply_markup=reply_markup)
    return WRITING

# Generate 20 words and prompt for essay
async def topic_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_topic = update.message.text
    context.user_data['selected_topic'] = user_topic
    
    # OpenAI API call to generate 20 words
    prompt = f"Generate 20 B1 level vocabulary words related to {user_topic}."
    response = openai.Completion.create(
        model="gpt-4o-mini",  # Updated model
        prompt=prompt,
        max_tokens=100
    )
    
    generated_words = response.choices[0].text.strip()
    context.user_data['generated_words'] = generated_words
    
    await update.message.reply_text(
        f"Write an essay on the topic: {user_topic}. Your essay must include the following words: {generated_words}. Minimum 250 words."
    )
    
    return ESSAY_SUBMISSION

# Submit essay and get feedback
async def submit_essay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_essay = update.message.text
    
    # OpenAI API call for feedback
    prompt = f"Analyze this essay:\n\n{user_essay}\n\nProvide feedback on grammar, vocabulary, structure, and cohesion."
    response = openai.Completion.create(
        model="gpt-4o-mini",
        prompt=prompt,
        max_tokens=300
    )
    
    feedback = response.choices[0].text.strip()
    await update.message.reply_text(f"Here is the feedback for your essay:\n\n{feedback}")
    
    return ConversationHandler.END

# Practice Tenses
async def practice_tenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sentences = [
        "At this time tomorrow, we _____ (fly) to Japan.",
        "By next year, they _____ (complete) the project."
    ]
    await update.message.reply_text(f"Fill in the blanks with the correct tense:\n{sentences[0]}")
    
    context.user_data['sentences'] = sentences
    return TENSES

# Check tense practice
async def check_tenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_answer = update.message.text.split(",")
    
    correct_answers = ["will be flying", "will have completed"]
    
    feedback = []
    for i, answer in enumerate(user_answer):
        if answer.strip() == correct_answers[i]:
            feedback.append(f"Sentence {i+1}: Correct")
        else:
            feedback.append(f"Sentence {i+1}: Incorrect. Correct answer is {correct_answers[i]}")
    
    await update.message.reply_text("\n".join(feedback))
    
    return ConversationHandler.END

# Start over with /start
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await start(update, context)

# Error handling
def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(f"Update {update} caused error {context.error}")

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WRITING: [
                MessageHandler(filters.Regex('^Writing Practice$'), writing_practice),
                MessageHandler(filters.Regex('^Practice Tenses$'), practice_tenses),
                MessageHandler(filters.TEXT & ~filters.COMMAND, topic_selected)
            ],
            ESSAY_SUBMISSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, submit_essay)],
            TENSES: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_tenses)]
        },
        fallbacks=[CommandHandler('start', restart)]
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
