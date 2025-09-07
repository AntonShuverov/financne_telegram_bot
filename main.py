import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from dotenv import load_dotenv
from database_extended import db
from ai_parser import ai_parser
from history_handler import (
    history_command, 
    refresh_history_callback,
    edit_transaction_callback,
    delete_transaction_callback,
    confirm_delete_callback
)

# Загружаем переменные из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Получаем токены
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def start(update: Update, context: CallbackContext):
    """Команда /start"""
    user = update.effective_user
    
    # Добавляем пользователя в базу
    db.add_user(user.id, user.username, user.first_name)
    
    welcome_message = f"""
🤖 Привет, {user.first_name}! Я твой финансовый помощник с ИИ.

📝 Просто пиши мне о своих тратах обычным языком:
- "купил кофе 800 тг"
- "потратил 5000 на продукты с каспи"
- "получил зарплату 350000"

🆕 **Новые команды:**
- /history - посмотреть историю транзакций
- /help - справка

Я автоматически распознаю суммы, категории и банки!
"""
    
    update.message.reply_text(welcome_message)

def help_command(update: Update, context: CallbackContext):
    """Команда /help"""
    help_text = """
🤖 **Финансовый бот с ИИ**

📝 **Как добавить трату:**
- "купил кофе 800 тг"
- "потратил 2500 на обед"
- "получил зарплату 350000"

📋 **Команды:**
- /history - история транзакций
- /help - эта справка

✏️ **В /history можете редактировать записи**
"""
    
    update.message.reply_text(help_text, parse_mode='Markdown')

def handle_message(update: Update, context: CallbackContext):
    """Обработка текстовых сообщений"""
    
    message_text = update.message.text
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    print(f"📩 Получено сообщение от {user_name}: {message_text}")
    
    # Добавляем пользователя в базу
    db.add_user(user_id, update.effective_user.username, user_name)
    
    # Парсим сообщение через ИИ
    ai_result = ai_parser.parse_transaction(message_text)
    
    if ai_result["success"]:
        # Подготавливаем данные для сохранения
        transaction_data = {
            'user_id': user_id,
            'amount': ai_result['amount'],
            'currency': ai_result.get('currency', 'KZT'),
            'category': ai_result['category'],
            'description': ai_result['description'],
            'bank': ai_result.get('bank'),
            'type': ai_result['type'],
            'confidence': ai_result['confidence'],
            'raw_message': message_text
        }
        
        # Сохраняем в базу данных
        if db.add_transaction(transaction_data):
            # Формируем ответ пользователю
            emoji = "💰" if ai_result['type'] == 'income' else "💸"
            
            response = f"""
{emoji} **Транзакция добавлена!**

💰 Сумма: {ai_result['amount']:,.0f} {ai_result['currency']}
🏷️ Категория: {ai_result['category']}
📝 Описание: {ai_result['description']}
"""
            
            if ai_result.get('bank'):
                response += f"🏦 Банк: {ai_result['bank']}\n"
            
            response += f"🎯 Уверенность: {ai_result['confidence']:.0%}\n"
            response += f"\n📋 Используйте /history для просмотра всех записей"
            
            update.message.reply_text(response, parse_mode='Markdown')
            
        else:
            update.message.reply_text("❌ Ошибка при сохранении транзакции.")
    else:
        # ИИ не смог распознать транзакцию
        response = f"""
🤔 Не удалось распознать финансовую операцию.

💡 **Попробуйте написать так:**
- "купил кофе 800 тг"
- "потратил 2500 на продукты"

❌ **Ошибка:** {ai_result.get('error', 'Неизвестная ошибка')}
"""
        
        update.message.reply_text(response, parse_mode='Markdown')

def error_handler(update: Update, context: CallbackContext):
    """Логирует ошибки"""
    logger.warning(f'Update {update} caused error {context.error}')

def main():
    """Запуск бота"""
    
    if not TELEGRAM_TOKEN:
        print("❌ Токен не найден! Проверьте .env файл")
        return
    
    if not OPENAI_API_KEY:
        print("❌ OpenAI API ключ не найден! Проверьте .env файл")
        return
    
    print("🚀 Запускаю финансового бота с историей...")
    
    # Создаем бота
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Добавляем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("history", history_command))  # НОВАЯ КОМАНДА
    
    # Добавляем обработчики сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # НОВЫЕ обработчики для истории
    dp.add_handler(CallbackQueryHandler(refresh_history_callback, pattern="^refresh_history$"))
    dp.add_handler(CallbackQueryHandler(edit_transaction_callback, pattern="^edit_\d+$"))
    dp.add_handler(CallbackQueryHandler(delete_transaction_callback, pattern="^delete_\d+$"))
    dp.add_handler(CallbackQueryHandler(confirm_delete_callback, pattern="^confirm_delete_\d+$"))
    
    # Добавляем обработчик ошибок
    dp.add_error_handler(error_handler)
    
    # Запускаем
    updater.start_polling()
    print("✅ Бот работает! Команды:")
    print("   📋 /history - история транзакций")
    print("   ❓ /help - справка")
    print("   🛑 Нажмите Ctrl+C для остановки")
    updater.idle()

if __name__ == '__main__':
    main()