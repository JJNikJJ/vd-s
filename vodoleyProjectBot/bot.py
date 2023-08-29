from config import TOKEN
from commands import *
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
)


def main() -> None:
    application = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", welcome), CommandHandler("signup", signup)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(register, pattern="^" + str(REGISTER) + "$"),
                CallbackQueryHandler(login, pattern="^" + str(LOGIN) + "$"),
                CallbackQueryHandler(service_action_coming, pattern="^" + str(SERVICE_ACTION_COMING) + "$"),
                CallbackQueryHandler(service_action_late, pattern="^" + str(SERVICE_ACTION_LATE) + "$"),
                CallbackQueryHandler(service_action_postpone, pattern="^" + str(SERVICE_ACTION_POSTPONE) + "$"),
                CallbackQueryHandler(service_action_cancel, pattern="^" + str(SERVICE_ACTION_CANCEL) + "$"),
                CallbackQueryHandler(service_action_tip, pattern="^" + str(SERVICE_ACTION_TIP) + "$"),
                CallbackQueryHandler(service_action_bonuses, pattern="^" + str(SERVICE_ACTION_BONUSES) + "$"),
            ],
            # END_ROUTES: [
            #     CallbackQueryHandler(end, pattern="^" + str(REGISTER) + "$"),
            #     CallbackQueryHandler(end, pattern="^" + str(LOGIN) + "$"),
            # ],
        },
        fallbacks=[CommandHandler("start", welcome)],
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
