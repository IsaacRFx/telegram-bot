from ctypes import cast
import logging
from html import unescape
import os
from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    
)
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    InlineQueryHandler,
    ConversationHandler,
    CallbackQueryHandler,
)
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from decouple import config
from uuid import uuid4
import requests
import json

ACCEPTED_TAGS = ['b','i','u','s','b','a','code','pre']

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOOSE, TYPING_REPLY, CANCEL = range(3)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo the user message."""
    logger.info("User %s: %s", update.message.from_user.full_name, update.message.text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""

    logger.info("User %s started the conversation. %s", update.message.from_user.full_name, update.message.from_user.id)
    keyboard = [
        [
            InlineKeyboardButton("StackOverflow", callback_data="stack"),
            InlineKeyboardButton("Reddit", callback_data="reddit"),
        ],
        [InlineKeyboardButton("Leave", callback_data="leave")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "What can I help you with?\n"
        "You can always type /cancel to stop talking to me.",
        reply_markup=reply_markup,
    )
    return CHOOSE

async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores the decision and sends it to API"""
    callbackData = update.callback_query
    await callbackData.answer(f"Option selected: {callbackData.data}")
    # logger.info("User %s: %s", user.first_name, update.message.text)
    if callbackData.data == "stack":
        await update.callback_query.message.edit_text(
            "It seems you've chosen StackOverflow. Please type your question."
        )
    if callbackData.data == "reddit":
        await update.callback_query.message.edit_text(
            "It seems you've chosen Reddit. Please type your question."
        )   
    if callbackData.data == "leave":
        await update.callback_query.message.edit_text(
            "Bye! I hope we can talk again some day."
        )
        return ConversationHandler.END

    return TYPING_REPLY


async def question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores the decision and sends it to API"""
    user = update.message.from_user
    userQuestion = update.message.text
    logger.info("Question of %s: %s", user.first_name, update.message.text)
    query = {"query": userQuestion}
    reply = requests.post('http://localhost:8000/api/scrape/', json=query).json()['results']
    readable_reply = str(reply).replace('<div>', '').replace('</div>', '').replace('<p>', '').replace('</p>', '').replace('<hr/>','').replace('<h2>','').replace('</h2>', '')
    print(readable_reply)
    await update.message.reply_text(text = readable_reply, parse_mode = ParseMode.HTML)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


if __name__ == "__main__":

    WEBHOOK = config("WEBHOOK", default=False, cast=bool)

    application = ApplicationBuilder().token(config("API_TOKEN")).build()
    logger.info("Starting bot")

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    convo = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^(?:devhelp init)$'), start)],
        states={
            CHOOSE: [CallbackQueryHandler(choose)],
            TYPING_REPLY: [MessageHandler(filters.TEXT & (~filters.COMMAND), question)],
            CANCEL: [MessageHandler(filters.TEXT, cancel)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(convo)
    application.add_handler(echo_handler)

    if WEBHOOK:
        logger.info("Starting webhook")
        application.run_webhook(
            listen="0.0.0.0",
            port=config("PORT"),
            url_path=config("API_TOKEN"),
            webhook_url=config("WEBHOOK_URL") + config("API_TOKEN"),
        )
    else:
        application.run_polling()
