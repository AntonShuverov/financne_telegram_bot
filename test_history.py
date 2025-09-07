from database_extended import db

def test_history_functionality():
    """Тестирование функций истории транзакций"""
    
    print("🧪 Тестируем функции истории...")
    
    # Тестовый пользователь
    user_id = 12345
    
    # Добавляем пользователя
    db.add_user(user_id, "test_user", "Test User")
    
    # Добавляем тестовые транзакции
    test_transactions = [
        {
            'user_id': user_id,
            'amount': 2500.0,
            'category': 'еда',
            'description': 'Обед в ресторане',
            'bank': 'kaspi',
            'type': 'expense'
        },
        {
            'user_id': user_id,
            'amount': 1200.0,
            'category': 'транспорт',
            'description': 'Такси домой',
            'type': 'expense'
        },
        {
            'user_id': user_id,
            'amount': 350000.0,
            'category': 'зарплата',
            'description': 'Зарплата за сентябрь',
            'type': 'income'
        }
    ]
    
    # Добавляем транзакции
    for trans in test_transactions:
        if db.add_transaction(trans):
            print(f"✅ Добавлена транзакция: {trans['description']}")
    
    # Получаем историю
    print("\n📋 Получаем историю транзакций:")
    history = db.get_user_transactions_history(user_id, limit=5)
    
    for i, trans in enumerate(history, 1):
        print(f"{i}. {trans['date']} - {trans['description']}: {trans['amount']} {trans['currency']} [{trans['category']}]")
    
    print("\n🎉 Тест функций истории завершен!")

if __name__ == "__main__":
    test_history_functionality()