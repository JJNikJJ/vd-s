import logging
import telegram
from vodoleyProjectBot import message_loader
from vodoleyProjectBot.functions import *
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (ContextTypes, ConversationHandler)
from django.utils import timezone


START_ROUTES = 1
REGISTER, LOGIN, SERVICE_ACTION_COMING, SERVICE_ACTION_LATE, SERVICE_ACTION_POSTPONE, SERVICE_ACTION_CANCEL, \
SERVICE_ACTION_TIP, SERVICE_ACTION_BONUSES = range(8)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
messages = message_loader.get_messages()


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    UpdateChatData(update.message.chat.username, update.message.chat.id)
    keyboard = [
        [InlineKeyboardButton("Зарегистрироваться", callback_data=str(REGISTER))],
        [InlineKeyboardButton("Войти", callback_data=str(LOGIN))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=messages['welcome'], reply_markup=reply_markup)
    return START_ROUTES


async def openwebapp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    UpdateChatData(update.message.chat.username, update.message.chat.id)
    keyboard = [
        [InlineKeyboardButton("Перейти в приложение",
                              web_app=WebAppInfo(url="https://vodoley.terexov.ru/#/auth"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=messages['openwebapp'], reply_markup=reply_markup)
    return ConversationHandler.END


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    UpdateChatData(query.message.chat.username, query.message.chat.id)
    username = query.message.chat.username
    await query.answer()
    keyboard = []

    userExists = GetUser(username)

    # debug
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=f"[DEBUG] User @{username}: {userExists}")

    if userExists:
        keyboard.append([InlineKeyboardButton("Войти", callback_data=str(LOGIN))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Вы уже зарегистрированы в сервисе, хотите войти?
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text=messages['user_exists'],
                                       reply_markup=reply_markup)
        return START_ROUTES
    else:
        keyboard.append([InlineKeyboardButton("Перейти в приложение",
                                              web_app=WebAppInfo(url=f"https://vodoley.terexov.ru/#/register?username={username}"))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Отлично! Чтобы зарегистрироваться в сервисе, воспользуйтесь приложением
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text=messages['registration_start'],
                                       reply_markup=reply_markup)
        return ConversationHandler.END


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    UpdateChatData(update.message.chat.username, update.message.chat.id)
    query = update.callback_query
    username = query.message.chat.username
    await query.answer()
    keyboard = []

    userExists = GetUser(username)

    # debug
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=f"[DEBUG] User @{username}: {userExists}")

    if userExists:
        keyboard = [
            [InlineKeyboardButton("Перейти в приложение",
                                  web_app=WebAppInfo(url=f"https://vodoley.terexov.ru/#/login?username={username}"))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Рады снова видеть вас в приложении
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text=f"{messages['nice_too_see_you_again']}@{username}",
                                       reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        keyboard.append([InlineKeyboardButton("Зарегистрироваться", callback_data=str(REGISTER))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Вы еще не зарегистрированы в сервисе, хотите пройти регистрацию?
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text=messages['user_not_found'],
                                       reply_markup=reply_markup)
        return START_ROUTES


# async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     query = update.callback_query
#     await query.answer()
#     return ConversationHandler.END


async def signup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    UpdateChatData(update.message.chat.username, update.message.chat.id)
    username = update.message.chat.username
    userExists = GetUser(username)
    keyboard = []

    if userExists:

        token = GetToken(userExists)
        active = GetActiveCheckout(userExists)

        if active:

            keyboard.append([InlineKeyboardButton("Приеду", callback_data=str(SERVICE_ACTION_COMING))])
            if not active.postponed:
                keyboard.append([InlineKeyboardButton("Опоздаю на 5-10 мин", callback_data=str(SERVICE_ACTION_LATE))])
            # keyboard.append([InlineKeyboardButton("Перенести запись", callback_data=str(SERVICE_ACTION_POSTPONE))])
            keyboard.append([InlineKeyboardButton("Отменить запись", callback_data=str(SERVICE_ACTION_CANCEL))])
            reply_markup = InlineKeyboardMarkup(keyboard)

            time_diff = active.target_datetime - timezone.localtime(timezone.now())
            await update.message.reply_text(text=f"[DEBUG]: ID - {active.id}")
            await update.message.reply_text(text=messages['reminder']
                                            .replace('$address', active.address.address)
                                            .replace('$service', "\n".join(obj.servicePrice.service.name for obj in
                                                                           active.services_list.all()))
                                            .replace('$car', f"{active.user.car.mark} {active.user.car.model}")
                                            .replace('$date', str(active.target_datetime.date()))
                                            .replace('$time', str(active.target_datetime.time()))
                                            .replace('$hours', str(time_diff.seconds // 3600))
                                            .replace('$minutes', str((time_diff.seconds // 60) % 60)),
                                            reply_markup=reply_markup,
                                            parse_mode=telegram.constants.ParseMode.HTML)
            return START_ROUTES
        else:
            keyboard.append([InlineKeyboardButton("Записаться",
                                                  web_app=WebAppInfo(url=f"https://vodoley.terexov.ru/#/makeorder?token={token[0]}"))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Записаться на мойку можно в нашем приложении
            await context.bot.send_message(chat_id=update.effective_user.id,
                                           text=messages['signup'],
                                           reply_markup=reply_markup)
            return ConversationHandler.END

    else:
        keyboard.append([InlineKeyboardButton("Зарегистрироваться", callback_data=str(REGISTER))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Вы еще не зарегистрированы в сервисе, хотите пройти регистрацию?
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text=messages['user_not_found'],
                                       reply_markup=reply_markup)
        return START_ROUTES


async def service_action_coming(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    UpdateChatData(query.message.chat.username, query.message.chat.id)
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_user.id, text=messages['see_you_soon'])
    return START_ROUTES


async def service_action_tip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    UpdateChatData(query.message.chat.username, query.message.chat.id)
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_user.id, text="Спасибо за чаевые! Ждем вас снова!")
    return ConversationHandler.END


async def service_action_bonuses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    UpdateChatData(query.message.chat.username, query.message.chat.id)
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_user.id, text="У вас пока нет бонусов")
    return ConversationHandler.END


# Опоздаю
async def service_action_late(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    UpdateChatData(query.message.chat.username, query.message.chat.id)
    await query.answer()
    user = GetUser(query.message.chat.username)
    if user:
        order = GetActiveCheckout(user)
        if order:
            PostponeOrder(order)
            await context.bot.send_message(chat_id=update.effective_user.id,
                                           text=messages['see_you_late']
                                           .replace('$time', order.target_datetime.time().strftime('%H:%M')))
            return ConversationHandler.END

    await context.bot.send_message(chat_id=update.effective_user.id, text="Ошибка: юзера или заказа не существует")
    return ConversationHandler.END


# Перенести (изменить)
async def service_action_postpone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    UpdateChatData(query.message.chat.username, query.message.chat.id)
    user = GetUser(query.message.chat.username)
    await query.answer()

    if user:
        order = GetActiveCheckout(user)
        if order:
            PostponeOrder(order)
            await context.bot.send_message(chat_id=update.effective_user.id, text=messages['service_postponed'])
            return ConversationHandler.END

    await context.bot.send_message(chat_id=update.effective_user.id, text="Ошибка: юзера или заказа не существует")
    return ConversationHandler.END


# Отменить
async def service_action_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    UpdateChatData(query.message.chat.username, query.message.chat.id)
    user = GetUser(query.message.chat.username)
    await query.answer()
    if user:
        order = GetActiveCheckout(user)
        if order:
            CancelOrder(order)
            await context.bot.send_message(chat_id=update.effective_user.id, text=messages['service_canceled'])
            return ConversationHandler.END

    await context.bot.send_message(chat_id=update.effective_user.id, text="Ошибка: юзера или заказа не существует")
    return ConversationHandler.END
