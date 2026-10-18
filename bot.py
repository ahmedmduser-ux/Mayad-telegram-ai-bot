import os
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN পাওয়া যায়নি")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY পাওয়া যায়নি")

client = OpenAI(api_key=OPENAI_API_KEY)

chat_histories = {}

SYSTEM_PROMPT = """
তুমি একজন বন্ধুসুলভ এবং সহায়ক AI assistant।
ব্যবহারকারী বাংলায় প্রশ্ন করলে বাংলায় উত্তর দেবে।
ইংরেজিতে প্রশ্ন করলে ইংরেজিতে উত্তর দেবে।
উত্তর পরিষ্কার, নির্ভুল এবং সহজভাবে দেবে।
"""

MAX_HISTORY_MESSAGES = 20

def split_message(text, max_length=4000):
    return [
        text[i:i + max_length]
        for i in range(0, len(text), max_length)
    ]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "আসসালামু আলাইকুম! আমি আপনার AI assistant।\n\n"
        "আমাকে যেকোনো প্রশ্ন করতে পারেন।\n"
        "নতুন conversation শুরু করতে /reset লিখুন।"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "আমি যেসব কাজ করতে পারি:\n\n"
        "• প্রশ্নের উত্তর দেওয়া\n"
        "• লেখালেখিতে সাহায্য করা\n"
        "• অনুবাদ করা\n"
        "• কোড লেখা ও ব্যাখ্যা করা\n"
        "• আইডিয়া দেওয়া\n\n"
        "নতুন chat শুরু করতে /reset লিখুন।"
    )

async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_histories[chat_id] = []

await update.message.reply_text(
        "আপনার conversation history মুছে ফেলা হয়েছে।"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

chat_id = update.effective_chat.id
    user_text = update.message.text.strip()

if not user_text:
        return

if chat_id not in chat_histories:
        chat_histories[chat_id] = []

history = chat_histories[chat_id]

history.append({
        "role": "user",
        "content": user_text
    })

history = history[-MAX_HISTORY_MESSAGES:]
    chat_histories[chat_id] = history

input_messages = [
        {
            "role": "developer",
            "content": SYSTEM_PROMPT
        }
    ] + history

try:
        await update.message.chat.send_action(
            action=ChatAction.TYPING
        )

response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-4.1-mini",
            input=input_messages
        )

answer = response.output_text.strip()

if not answer:
            answer = "দুঃখিত, কোনো উত্তর তৈরি করা যায়নি।"

history.append({
            "role": "assistant",
            "content": answer
        })

chat_histories[chat_id] = history[-MAX_HISTORY_MESSAGES:]

for part in split_message(answer):
            await update.message.reply_text(part)

except Exception as error:
        print("Error:", repr(error))

await update.message.reply_text(
            "দুঃখিত, এখন উত্তর দিতে সমস্যা হচ্ছে। "
            "কিছুক্ষণ পরে আবার চেষ্টা করুন।"
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("Telegram error:", repr(context.error))

def main():
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

application.add_handler(
        CommandHandler("start", start)
    )

application.add_handler(
        CommandHandler("help", help_command)
    )

application.add_handler(
        CommandHandler("reset", reset_chat)
    )

application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

application.add_error_handler(error_handler)

print("Telegram AI bot চালু হয়েছে...")
    application.run_polling()

if __name__ == "__main__":
    main()
