from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database_extended import db
from datetime import datetime, timedelta
import calendar

def statistics_command(update: Update, context: CallbackContext):
    """Команда /stats - статистика по дням"""
    
    user_id = update.effective_user.id
    today = datetime.now().date()
    
    # Показываем статистику за сегодня
    show_daily_statistics(update, context, user_id, today)

def show_daily_statistics(update, context, user_id: int, date):
    """Показать статистику за конкретный день"""
    
    # Получаем транзакции за день
    daily_transactions = db.get_transactions_by_date(user_id, date)
    
    # Подсчитываем суммы
    total_expenses = sum(t['amount'] for t in daily_transactions if t['type'] == 'expense')
    total_income = sum(t['amount'] for t in daily_transactions if t['type'] == 'income')
    transfers = [t for t in daily_transactions if t['type'] == 'transfer']
    
    # Форматируем дату
    date_str = date.strftime("%d.%m.%Y")
    weekday = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][date.weekday()]
    
    message = f"📊 *Статистика за {weekday}, {date_str}:*\n\n"
    
    # Балансы карт
    balances = db.get_account_balances(user_id)
    if balances:
        message += "💳 *Текущие балансы:*\n"
        for balance in balances:
            emoji = "💳" if "kaspi" in balance['account_name'].lower() or "halyk" in balance['account_name'].lower() else "💵"
            message += f"{emoji} {balance['account_name']}: {balance['balance']:,.0f} {balance['currency']}\n"
        message += "\n"
    
    # Доходы и расходы
    if total_income > 0:
        message += f"💰 *Доходы:* {total_income:,.0f} тг\n"
    
    if total_expenses > 0:
        message += f"💸 *Расходы:* {total_expenses:,.0f} тг\n"
    
    if total_income > 0 or total_expenses > 0:
        balance = total_income - total_expenses
        emoji = "📈" if balance >= 0 else "📉"
        message += f"{emoji} *Баланс дня:* {balance:+,.0f} тг\n\n"
    
    # Переводы
    if transfers:
        message += "🔄 *Переводы:*\n"
        for transfer in transfers:
            message += f"• {transfer['description']}: {transfer['amount']:,.0f} тг\n"
        message += "\n"
    
    # Детализация трат
    if daily_transactions:
        expenses = [t for t in daily_transactions if t['type'] == 'expense']
        income = [t for t in daily_transactions if t['type'] == 'income']
        
        if expenses:
            message += "💸 *Детализация расходов:*\n"
            for trans in expenses:
                bank_info = f" ({trans['bank']})" if trans['bank'] else ""
                message += f"• {trans['description']}: {trans['amount']:,.0f} тг{bank_info}\n"
            message += "\n"
        
        if income:
            message += "💰 *Детализация доходов:*\n"
            for trans in income:
                bank_info = f" ({trans['bank']})" if trans['bank'] else ""
                message += f"• {trans['description']}: {trans['amount']:,.0f} тг{bank_info}\n"
            message += "\n"
    else:
        message += "📝 *Операций за этот день не было*\n\n"
    
    # Создаем кнопки навигации
    keyboard = create_date_navigation_keyboard(date)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем или редактируем сообщение
    if hasattr(update, 'callback_query') and update.callback_query:
        update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

def create_date_navigation_keyboard(current_date):
    """Создать клавиатуру навигации по датам"""
    
    # Навигация по дням
    prev_day = current_date - timedelta(days=1)
    next_day = current_date + timedelta(days=1)
    today = datetime.now().date()
    
    keyboard = []
    
    # Кнопки переключения дней
    day_row = []
    day_row.append(InlineKeyboardButton(
        f"← {prev_day.strftime('%d.%m')}", 
        callback_data=f"stats_day_{prev_day.strftime('%Y-%m-%d')}"
    ))
    
    if current_date != today:
        day_row.append(InlineKeyboardButton(
            "📅 Сегодня", 
            callback_data=f"stats_day_{today.strftime('%Y-%m-%d')}"
        ))
    else:
        day_row.append(InlineKeyboardButton(
            "📅 Сегодня ●", 
            callback_data=f"stats_day_{today.strftime('%Y-%m-%d')}"
        ))
    
    day_row.append(InlineKeyboardButton(
        f"{next_day.strftime('%d.%m')} →", 
        callback_data=f"stats_day_{next_day.strftime('%Y-%m-%d')}"
    ))
    
    keyboard.append(day_row)
    
    # Кнопки переключения месяцев
    current_month = current_date.replace(day=1)
    prev_month = (current_month - timedelta(days=1)).replace(day=1)
    next_month = current_month.replace(day=28) + timedelta(days=4)
    next_month = next_month.replace(day=1)
    
    month_row = []
    month_row.append(InlineKeyboardButton(
        f"← {prev_month.strftime('%b')}",
        callback_data=f"stats_month_{prev_month.strftime('%Y-%m')}"
    ))
    
    month_row.append(InlineKeyboardButton(
        f"📅 {current_month.strftime('%B %Y')}",
        callback_data=f"stats_month_{current_month.strftime('%Y-%m')}"
    ))
    
    month_row.append(InlineKeyboardButton(
        f"{next_month.strftime('%b')} →",
        callback_data=f"stats_month_{next_month.strftime('%Y-%m')}"
    ))
    
    keyboard.append(month_row)
    
    # Быстрые фильтры
    filter_row = []
    filter_row.append(InlineKeyboardButton("📊 Неделя", callback_data="stats_week"))
    filter_row.append(InlineKeyboardButton("📈 Месяц", callback_data="stats_month_summary"))
    filter_row.append(InlineKeyboardButton("🔄 Обновить", callback_data=f"stats_day_{current_date.strftime('%Y-%m-%d')}"))
    
    keyboard.append(filter_row)
    
    return keyboard

def stats_day_callback(update: Update, context: CallbackContext):
    """Обработка переключения дня"""
    
    query = update.callback_query
    query.answer()
    
    # Извлекаем дату из callback_data
    date_str = query.data.split('_')[2]  # stats_day_2025-09-07
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    user_id = update.effective_user.id
    show_daily_statistics(update, context, user_id, date)

def stats_month_callback(update: Update, context: CallbackContext):
    """Обработка переключения месяца"""
    
    query = update.callback_query
    query.answer()
    
    # Извлекаем месяц из callback_data  
    month_str = query.data.split('_')[2]  # stats_month_2025-09
    year, month = map(int, month_str.split('-'))
    
    # Показываем первый день месяца
    first_day = datetime(year, month, 1).date()
    
    user_id = update.effective_user.id
    show_daily_statistics(update, context, user_id, first_day)

def stats_week_callback(update: Update, context: CallbackContext):
    """Статистика за неделю"""
    
    query = update.callback_query
    query.answer()
    
    user_id = update.effective_user.id
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    # Получаем транзакции за неделю
    week_transactions = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_transactions = db.get_transactions_by_date(user_id, day)
        week_transactions.extend(day_transactions)
    
    total_expenses = sum(t['amount'] for t in week_transactions if t['type'] == 'expense')
    total_income = sum(t['amount'] for t in week_transactions if t['type'] == 'income')
    
    message = f"📊 *Статистика за неделю*\n"
    message += f"({week_start.strftime('%d.%m')} - {(week_start + timedelta(days=6)).strftime('%d.%m')})\n\n"
    message += f"💰 Доходы: {total_income:,.0f} тг\n"
    message += f"💸 Расходы: {total_expenses:,.0f} тг\n"
    message += f"📈 Баланс: {total_income - total_expenses:+,.0f} тг\n\n"
    
    # Группируем по категориям
    categories = {}
    for trans in week_transactions:
        if trans['type'] == 'expense':
            cat = trans['category']
            categories[cat] = categories.get(cat, 0) + trans['amount']
    
    if categories:
        message += "🏷️ *По категориям:*\n"
        for cat, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total_expenses) * 100 if total_expenses > 0 else 0
            message += f"• {cat}: {amount:,.0f} тг ({percentage:.1f}%)\n"
    
    keyboard = [[InlineKeyboardButton("← Назад к дням", callback_data=f"stats_day_{today.strftime('%Y-%m-%d')}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

def stats_month_summary_callback(update: Update, context: CallbackContext):
    """Статистика за месяц"""
    
    query = update.callback_query
    query.answer()
    
    user_id = update.effective_user.id
    today = datetime.now().date()
    month_start = today.replace(day=1)
    
    # Получаем статистику за месяц
    month_stats = db.get_user_statistics(user_id, period_days=30)
    
    message = f"📊 *Статистика за {month_start.strftime('%B %Y')}*\n\n"
    message += f"💰 Доходы: {month_stats['total_income']:,.0f} тг\n"
    message += f"💸 Расходы: {month_stats['total_expenses']:,.0f} тг\n"
    message += f"📈 Баланс: {month_stats['total_income'] - month_stats['total_expenses']:+,.0f} тг\n\n"
    
    if month_stats['expenses_by_category']:
        message += "🏷️ *Расходы по категориям:*\n"
        for cat_stat in month_stats['expenses_by_category']:
            percentage = (cat_stat['amount'] / month_stats['total_expenses']) * 100
            message += f"• {cat_stat['category']}: {cat_stat['amount']:,.0f} тг ({percentage:.1f}%)\n"
    
    keyboard = [[InlineKeyboardButton("← Назад к дням", callback_data=f"stats_day_{today.strftime('%Y-%m-%d')}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')