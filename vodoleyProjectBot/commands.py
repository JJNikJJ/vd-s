import logging
import message_loader
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (ContextTypes, ConversationHandler)
from functions import *


START_ROUTES = 1
REGISTER, LOGIN, SERVICE_ACTION_COMING, SERVICE_ACTION_LATE, SERVICE_ACTION_POSTPONE, SERVICE_ACTION_CANCEL, \
    SERVICE_ACTION_TIP, SERVICE_ACTION_BONUSES = range(8)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
messages = message_loader.get_messages()


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Зарегистрироваться", callback_data=str(REGISTER))],
        [InlineKeyboardButton("Войти", callback_data=str(LOGIN))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=messages['welcome'], reply_markup=reply_markup)
    return START_ROUTES


# async def openwebapp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    username = query.message.chat.username
    await query.answer()
    keyboard = []
    if IsUserExist(username):
        keyboard.append([InlineKeyboardButton("Войти", callback_data=str(LOGIN))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text=messages['user_exists'],
                                       reply_markup=reply_markup)
    else:
        keyboard.append([InlineKeyboardButton("Перейти в приложение",
                                              web_app=WebAppInfo(url="https://vodoley.terexov.ru/#/auth"))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text=messages['registration_start'])
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text=messages['registration_complete'],
                                       reply_markup=reply_markup)

    return ConversationHandler.END


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    username = query.message.chat.username
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=f"Привет, {query.message.chat.username}")

    keyboard = [
        [InlineKeyboardButton("Перейти в приложение",
                              web_app=WebAppInfo(url="https://vodoley.terexov.ru/#/auth"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=f"{messages['nice_too_see_you_again']}@{username}",
                                   reply_markup=reply_markup)
    return ConversationHandler.END


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return ConversationHandler.END


async def signup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Приеду", callback_data=str(SERVICE_ACTION_COMING))],
        [InlineKeyboardButton("Опоздаю на 5-10 мин", callback_data=str(SERVICE_ACTION_LATE))],
        [InlineKeyboardButton("Перенести запись", callback_data=str(SERVICE_ACTION_POSTPONE))],
        [InlineKeyboardButton("Отменить запись", callback_data=str(SERVICE_ACTION_CANCEL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=messages['reminder'], reply_markup=reply_markup)
    return START_ROUTES


async def service_action_coming(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_user.id, text=messages['see_you_soon'])
    await context.bot.send_message(chat_id=update.effective_user.id, text=messages['service_started'])
    await context.bot.send_message(chat_id=update.effective_user.id, text=messages['service_will_end_soon'])
    keyboard = [
        [InlineKeyboardButton("Оставить чаевые", callback_data=str(SERVICE_ACTION_TIP))],
        [InlineKeyboardButton("Посмотреть мои скидки", callback_data=str(SERVICE_ACTION_BONUSES))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=messages['service_complete'],
        reply_markup=reply_markup)
    return START_ROUTES


async def service_action_tip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_user.id, text="Спасибо за чаевые! Ждем вас снова!")
    return ConversationHandler.END


async def service_action_bonuses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_user.id, text="У вас пока нет бонусов")
    return ConversationHandler.END


async def service_action_late(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_user.id, text=messages['see_you_late'])
    return ConversationHandler.END


async def service_action_postpone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_user.id, text=messages['service_postponed'])
    return ConversationHandler.END


async def service_action_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_user.id, text=messages['service_canceled'])
    return ConversationHandler.END
