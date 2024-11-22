from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import random
import time
import boto3

import spotywrapper as wr

BOT_NAME = "Amador"


# Get current time



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    dynamic_greetings = [
        "Hey there!",
        "Hello!",
        "Hi!",
        "Hola!",
        "Greetings!",
        "Hey!",
        "Howdy!",
    ]

    greeting = random.choice(dynamic_greetings)
    # music icon emoji
    check_emoji = "\U0001F3B5"
    init_msg = f"{greeting}! I'm {BOT_NAME}, your Spotify amigo.\n"
    init_msg+= f"Tell me Your Spotify ID to enter the world of music.{check_emoji},\n eg. /id init YourSpotifyId" 
    await update.message.reply_text(init_msg)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id

    raw_input = update.message.text
    proccesed = "".join(raw_input.split()).lower()
    i = 0
    match proccesed:
         case "monthly": 
            msg=''
            chat_id = update.message.chat_id
            data = get_spotify_data(chat_id)
        
            if data:
              msg=f'Here are your favourite songs from the last month:\n'
              for track in data:
               
                msg+=f"{i+1}.{track['track_name']} by {track['artist_name']}\n"
                i+=1
            else:
             msg = "You haven't listened to any songs on Spotify yet."
       
            await context.bot.send_message(chat_id=chat_id, text=msg)
            return
    
    
    await context.bot.send_message(chat_id=chat_id, text='hola que tal')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("I can help you with Spotify! Just send me a message.")


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    error_msg = "Please provide a valid command.\nType /help for more information."
    if len(update.message.text.split(" ")) < 3:
            await update.message.reply_text(error_msg)
            return
    if update.message.text.split(" ")[1] != "init":
            await update.message.reply_text(error_msg)
            return
    try:
        
        chat_id = update.message.chat_id

        spotify_id = update.message.text.split(" ")[2]

        dybamodb = boto3.resource('dynamodb', region_name='eu-north-1')
        chat_ids_table = dybamodb.Table('telegram-ids')
        chat_ids_table.put_item(Item={'chat_id': str(chat_id), 'spotify_id': str(spotify_id)})

        check_mark = "\U00002705"
        await  update.message.reply_text(f"Congratulations! You have successfully linked your Spotify account with your Telegram account.{check_mark}") 
    except Exception as e:
        print(e)
        await update.message.reply_text(error_msg)


def get_spotify_data(chat_id):
    tracks = wr.get_user_data(chat_id)

    return tracks

async def send_message_to_all(context: ContextTypes.DEFAULT_TYPE) -> None:
    dynamo = boto3.resource('dynamodb', region_name='eu-north-1')
    chat_ids_table = dynamo.Table('telegram-ids')
    response = chat_ids_table.scan()
    i = 0
    for item in response['Items']:
        msg=''
        chat_id = item['chat_id']
        data = get_spotify_data(chat_id)
        
        if data:
            msg = f"Here are the songs you have listened to on Spotify:\n"
            msg+=f"{i+1}. {data['track_name']} by {data['artist_name']}\n"
            i+=1
        else:
            msg = "You haven't listened to any songs on Spotify yet."
       
        await context.bot.send_message(chat_id=chat_id, text=msg)


if __name__ == "__main__":
    # Replace 'YOUR_BOT_TOKEN' with your actual token
    bot_token = os.environ.get("TELEGRAM_ACCESS")
   
    
    # Create the application
    app = ApplicationBuilder().token(bot_token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(CommandHandler("id", id_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Schedule a job to send messages periodically

    #job_queue = app.job_queue
    #job_queue.run_repeating(send_message_to_all, interval=60, first=10)  # Send message every 60 seconds

    # Start the bot
    app.run_polling()
