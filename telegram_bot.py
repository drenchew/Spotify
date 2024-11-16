from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import random
import time



BOT_NAME = "Amador"
chat_ids = set()  # Store chat IDs

# Get current time
def get_current_time():
    return time.strftime("%H:%M:%S", time.localtime())

# Define a start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    chat_ids.add(chat_id)  # Store the chat ID
    init_msg = f"Hola! I'm {BOT_NAME}, your Spotify amigo."
    await update.message.reply_text(init_msg)

# Define an echo handler for regular messages
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    chat_ids.add(chat_id)  # Store the chat ID
    user_message = update.message.text
    if user_message.lower() == "weekly":
        txt = "Here's your most listened songs!"
    await update.message.reply_text(f"{txt}")

# Define a help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Use /start to begin chatting with me. Send any message, and I'll echo it!")

# Function to send messages to all stored chat IDs
async def send_message_to_all(context: ContextTypes.DEFAULT_TYPE) -> None:
    for chat_id in chat_ids:
        await context.bot.send_message(chat_id=chat_id, text="Еее чувяк!")

if __name__ == "__main__":
    # Replace 'YOUR_BOT_TOKEN' with your actual token
    bot_token = os.environ.get("TELEGRAM_ACCESS")
    bot_token = "8073895496:AAGIAlOYyMUj7KbPPQGLdn6SO8_dmch_2Fk"
    
    # Create the application
    app = ApplicationBuilder().token(bot_token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Schedule a job to send messages periodically
    job_queue = app.job_queue
    job_queue.run_repeating(send_message_to_all, interval=60, first=10)  # Send message every 60 seconds

    # Start the bot
    app.run_polling()
