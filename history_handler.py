from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database_extended import db
from datetime import datetime

def history_command(update: Update, context: CallbackContext):
    """Команда /history - показать последние транзакции"""
    
    user_id = update.effective_user.id
    
    # Получаем историю транзакций
    history = db.get_user_transactions_history(user_id, limit=10)
    
    if not history:
        update.message.reply_text(
            "📋 История транзакций пуста.\n\n"
            "Начните добавлять транзакции, просто написав:\n"
            "💡 \"купил кофе 800 тг\"\n"
            "💡 \"потратил 2500 на обед\""
        )
        return
    
    # Формируем сообщение с историей
    message = "📋 *Ваши последние транзакции:*\n\n"
    
    keyboard = []
    
    for i, trans in enumerate(history, 1):
        # Форматируем дату
        if isinstance(trans['date'], str):
            date_str = trans['date']
        else:
            date_str = str(trans['date'])
        
        # Эмодзи для типа транзакции
        emoji = "💰" if trans['type'] == 'income' else "💸"
        
        # Добавляем строку транзакции
        message += f"{i}. {emoji} *{trans['amount']:,.0f} {trans['currency']}*\n"
        message += f"   📅 {date_str} • 🏷️ {trans['category']}\n"
        message += f"   📝 {trans['description']}\n"
        
        if trans['bank']:
            message += f"   🏦 {trans['bank']}\n"
        
        message += "\n"
        
        # Добавляем кнопки для каждой транзакции
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ Редактировать #{i}", 
                callback_data=f"edit_{trans['id']}"
            ),
            InlineKeyboardButton(
                f"🗑️ Удалить #{i}", 
                callback_data=f"delete_{trans['id']}"
            )
        ])
    
    # Добавляем кнопки навигации
    keyboard.append([
        InlineKeyboardButton("🔄 Обновить", callback_data="refresh_history"),
        InlineKeyboardButton("📊 Статистика", callback_data="show_stats")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        message, 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def refresh_history_callback(update: Update, context: CallbackContext):
    """Обновить историю транзакций"""
    
    query = update.callback_query
    query.answer()
    
    user_id = update.effective_user.id
    
    # Получаем обновленную историю
    history = db.get_user_transactions_history(user_id, limit=10)
    
    if not history:
        query.edit_message_text(
            "📋 История транзакций пуста.\n\n"
            "Начните добавлять транзакции, просто написав:\n"
            "💡 \"купил кофе 800 тг\""
        )
        return
    
    # Формируем обновленное сообщение
    message = "📋 *Ваши последние транзакции:* _(обновлено)_\n\n"
    
    keyboard = []
    
    for i, trans in enumerate(history, 1):
        # Форматируем дату
        if isinstance(trans['date'], str):
            date_str = trans['date']
        else:
            date_str = str(trans['date'])
        
        # Эмодзи для типа транзакции
        emoji = "💰" if trans['type'] == 'income' else "💸"
        
        # Добавляем строку транзакции
        message += f"{i}. {emoji} *{trans['amount']:,.0f} {trans['currency']}*\n"
        message += f"   📅 {date_str} • 🏷️ {trans['category']}\n"
        message += f"   📝 {trans['description']}\n"
        
        if trans['bank']:
            message += f"   🏦 {trans['bank']}\n"
        
        message += "\n"
        
        # Добавляем кнопки для каждой транзакции
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ Редактировать #{i}", 
                callback_data=f"edit_{trans['id']}"
            ),
            InlineKeyboardButton(
                f"🗑️ Удалить #{i}", 
                callback_data=f"delete_{trans['id']}"
            )
        ])
    
    # Добавляем кнопки навигации
    keyboard.append([
        InlineKeyboardButton("🔄 Обновить", callback_data="refresh_history"),
        InlineKeyboardButton("📊 Статистика", callback_data="show_stats")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        message, 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def edit_transaction_callback(update: Update, context: CallbackContext):
    """Начать редактирование транзакции"""
    
    query = update.callback_query
    query.answer()
    
    # Извлекаем ID транзакции из callback_data
    transaction_id = int(query.data.split('_')[1])
    user_id = update.effective_user.id
    
    # Получаем данные транзакции
    transaction = db.get_transaction_by_id(transaction_id, user_id)
    
    if not transaction:
        query.edit_message_text(
            "❌ Транзакция не найдена или была удалена."
        )
        return
    
    # Показываем меню редактирования
    message = f"✏️ *Редактирование транзакции:*\n\n"
    message += f"💰 Сумма: {transaction['amount']} {transaction['currency']}\n"
    message += f"🏷️ Категория: {transaction['category']}\n"
    message += f"📝 Описание: {transaction['description']}\n"
    message += f"🏦 Банк: {transaction['bank'] or 'Не указан'}\n"
    message += f"📅 Дата: {transaction['date']}\n\n"
    message += "Что хотите изменить?"
    
    keyboard = [
        [
            InlineKeyboardButton("💰 Сумму", callback_data=f"edit_amount_{transaction_id}"),
            InlineKeyboardButton("🏷️ Категорию", callback_data=f"edit_category_{transaction_id}")
        ],
        [
            InlineKeyboardButton("📝 Описание", callback_data=f"edit_description_{transaction_id}"),
            InlineKeyboardButton("🏦 Банк", callback_data=f"edit_bank_{transaction_id}")
        ],
        [
            InlineKeyboardButton("❌ Отмена", callback_data="refresh_history")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def delete_transaction_callback(update: Update, context: CallbackContext):
    """Подтверждение удаления транзакции"""
    
    query = update.callback_query
    query.answer()
    
    # Извлекаем ID транзакции
    transaction_id = int(query.data.split('_')[1])
    user_id = update.effective_user.id
    
    # Получаем данные транзакции для подтверждения
    transaction = db.get_transaction_by_id(transaction_id, user_id)
    
    if not transaction:
        query.edit_message_text(
            "❌ Транзакция не найдена или была удалена."
        )
        return
    
    # Показываем подтверждение удаления
    message = f"🗑️ *Подтвердите удаление:*\n\n"
    message += f"💰 Сумма: {transaction['amount']} {transaction['currency']}\n"
    message += f"🏷️ Категория: {transaction['category']}\n"
    message += f"📝 Описание: {transaction['description']}\n"
    message += f"📅 Дата: {transaction['date']}\n\n"
    message += "⚠️ Это действие нельзя отменить!"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{transaction_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data="refresh_history")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def confirm_delete_callback(update: Update, context: CallbackContext):
    """Окончательное удаление транзакции"""
    
    query = update.callback_query
    query.answer()
    
    # Извлекаем ID транзакции
    transaction_id = int(query.data.split('_')[2])
    user_id = update.effective_user.id
    
    # Удаляем транзакцию
    if db.delete_transaction(transaction_id, user_id):
        query.edit_message_text(
            "✅ Транзакция успешно удалена!\n\n"
            "Используйте /history чтобы посмотреть обновленную историю."
        )
    else:
        query.edit_message_text(
            "❌ Ошибка при удалении транзакции.\n\n"
            "Попробуйте еще раз или обратитесь в поддержку."
        )