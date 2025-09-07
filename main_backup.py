import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, CallbackContext
from dotenv import load_dotenv
from database import db
from ai_parser import ai_parser

# Загружаем переменные из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Получаем токены
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def start(update: Update, context: CallbackContext):
    """Команда /start"""
    user = update.effective_user
    
    # Добавляем пользователя в базу
    db.add_user(user.id, user.username, user.first_name)
    db.add_default_categories(user.id)
    
    # Создаем кнопки
    keyboard = [
        [InlineKeyboardButton("💸 Расходы", callback_data='expenses')],
        [InlineKeyboardButton("💰 Доходы", callback_data='income')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')],
        [InlineKeyboardButton("🤖 Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = """
🤖 Привет! Я твой финансовый помощник с ИИ.

📝 Просто пиши мне о своих тратах обычным языком:
• "купил кофе 800 тг"
• "потратил 5000 на продукты с каспи"
• "получил зарплату 350000"

Я автоматически распознаю суммы, категории и банки! 💸
"""
    
    update.message.reply_text(welcome_message, reply_markup=reply_markup)

def handle_message(update: Update, context: CallbackContext):
    """Обработка текстовых сообщений с ИИ"""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    print(f"💬 Получено сообщение от {user_id}: {user_message}")
    
    # Парсим сообщение через ИИ
    parsed_data = ai_parser.parse_transaction(user_message)
    
    if parsed_data["success"] and parsed_data["amount"] is not None:
        # Сохраняем транзакцию в базу
        transaction_id = db.add_transaction(
            user_id=user_id,
            amount=parsed_data["amount"],
            currency=parsed_data["currency"],
            category=parsed_data["category"],
            description=parsed_data["description"],
            bank=parsed_data["bank"],
            transaction_type=parsed_data["type"]
        )
        
        # Формируем ответ
        transaction_type = "💰 Доход" if parsed_data["type"] == "income" else "💸 Расход"
        bank_info = f" ({parsed_data['bank']})" if parsed_data['bank'] else ""
        
        response = f"""✅ Добавил транзакцию:

{transaction_type}: {parsed_data['amount']} {parsed_data['currency']}
🏷️ Категория: {parsed_data['category']}
📝 Описание: {parsed_data['description']}{bank_info}
🎯 Уверенность: {parsed_data['confidence']:.0%}

ID транзакции: {transaction_id}"""
        
        # Добавляем кнопки для быстрых действий
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data='stats')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(response, reply_markup=reply_markup)
        
    elif parsed_data["success"] and parsed_data["amount"] is None:
        # ИИ не смог определить сумму
        response = f"""🤔 Я понял, что это {parsed_data['category']}, но не смог определить сумму.

Попробуйте написать более конкретно, например:
• "потратил 2500 на {parsed_data['category']}"
• "купил {parsed_data['description']} за 1500 тг"
"""
        update.message.reply_text(response)
        
    else:
        # Ошибка парсинга
        response = f"""❌ Не смог распознать финансовую операцию.

Попробуйте написать так:
• "потратил 2500 на кофе"
• "купил продукты за 15000 тг"
• "получил зарплату 400000"
• "такси домой 1200 с каспи"

Ошибка: {parsed_data.get('error', 'Неизвестная ошибка')}"""
        
        update.message.reply_text(response)

def button_callback(update: Update, context: CallbackContext):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == 'main_menu':
        # Возврат в главное меню
        keyboard = [
            [InlineKeyboardButton("💸 Расходы", callback_data='expenses')],
            [InlineKeyboardButton("💰 Доходы", callback_data='income')],
            [InlineKeyboardButton("📊 Статистика", callback_data='stats')],
            [InlineKeyboardButton("🤖 Помощь", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text("🏠 Главное меню:", reply_markup=reply_markup)
        
    elif query.data == 'stats':
        # Показать статистику
        from datetime import datetime
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Получаем статистику по расходам
        expense_stats = db.get_category_stats(user_id, current_month, current_year, "expense")
        income_stats = db.get_category_stats(user_id, current_month, current_year, "income")
        
        stats_text = f"📊 Статистика за {current_month}.{current_year}\n\n"
        
        if expense_stats:
            total_expenses = sum(stat['total'] for stat in expense_stats)
            stats_text += f"💸 РАСХОДЫ: {total_expenses:,.0f} тг\n"
            for stat in expense_stats[:5]:  # Топ-5 категорий
                stats_text += f"  🏷️ {stat['category']}: {stat['total']:,.0f} тг\n"
            stats_text += "\n"
        
        if income_stats:
            total_income = sum(stat['total'] for stat in income_stats)
            stats_text += f"💰 ДОХОДЫ: {total_income:,.0f} тг\n"
            for stat in income_stats[:3]:  # Топ-3 источника
                stats_text += f"  🏷️ {stat['category']}: {stat['total']:,.0f} тг\n"
            stats_text += "\n"
        
        if expense_stats and income_stats:
            balance = sum(stat['total'] for stat in income_stats) - sum(stat['total'] for stat in expense_stats)
            balance_emoji = "📈" if balance >= 0 else "📉"
            stats_text += f"{balance_emoji} БАЛАНС: {balance:,.0f} тг"
        
        if not expense_stats and not income_stats:
            stats_text += "Пока нет транзакций за этот месяц.\nНапишите о своих тратах, и я их сохраню!"
        
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(stats_text, reply_markup=reply_markup)
        
    elif query.data == 'help':
        help_text = """🤖 Как пользоваться ботом:

📝 ДОБАВЛЕНИЕ ТРАТ:
Просто пишите естественным языком:
• "потратил 2500 на кофе"
• "купил продукты 15000 тг с каспи"
• "такси домой 1200"
• "получил зарплату 400000"

🎯 Я автоматически определю:
• Сумму и валюту
• Категорию (еда, транспорт, и т.д.)
• Банк/карту
• Тип операции (доход/расход)

📊 СТАТИСТИКА:
Нажмите "Статистика" чтобы увидеть:
• Общие расходы и доходы
• Топ категорий трат
• Баланс за месяц

🚀 Просто говорите со мной как с обычным человеком!"""
        
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(help_text, reply_markup=reply_markup)

def error_handler(update: Update, context: CallbackContext):
    """Обработка ошибок"""
    logging.warning(f'Update {update} caused error {context.error}')

def main():
    """Запуск бота"""
    print("🚀 Запускаю финансового бота с ИИ...")
    
    # Проверяем токены
    if not TELEGRAM_TOKEN:
        print("❌ Токен Telegram не найден в .env файле!")
        return
    
    # Создаем бота
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Добавляем обработчики
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button_callback))
    dp.add_error_handler(error_handler)
    
    # Запускаем
    updater.start_polling()
    print("✅ Финансовый бот работает! Ctrl+C для остановки")
    print("💡 Напишите боту о своих тратах, и он их автоматически сохранит!")
    updater.idle()

if __name__ == '__main__':
    main()