from datetime import datetime

def test_database_extended():
    """Тест новых методов базы данных"""
    print("🧪 Тестируем расширенную базу данных...")
    
    try:
        from database_extended import db
        
        # Проверяем новые методы
        new_methods = [
            'get_transactions_by_date',
            'add_transfer',
            'update_account_balance',
            'get_account_balances',
            'add_account_balance'
        ]
        
        print("🔍 Проверяем новые методы:")
        missing_methods = []
        for method in new_methods:
            if hasattr(db, method):
                print(f"   ✅ {method}")
            else:
                print(f"   ❌ {method} - ОТСУТСТВУЕТ")
                missing_methods.append(method)
        
        if missing_methods:
            print(f"\n💡 Нужно добавить методы: {missing_methods}")
            return False
        
        # Тестируем добавление баланса
        print("\n💳 Тестируем балансы счетов:")
        user_id = 99999  # тестовый пользователь
        
        # Добавляем пользователя
        db.add_user(user_id, "test_user", "Test User")
        
        # Добавляем балансы
        test_balances = [
            ("Kaspi", 150000),
            ("Halyk", 80000),
            ("Наличные", 25000)
        ]
        
        for account, balance in test_balances:
            result = db.add_account_balance(user_id, account, balance)
            status = "✅" if result else "❌"
            print(f"   {status} {account}: {balance:,} тг")
        
        # Получаем балансы
        balances = db.get_account_balances(user_id)
        print(f"\n📊 Получено балансов: {len(balances)}")
        for balance in balances:
            print(f"   💳 {balance['account_name']}: {balance['balance']:,.0f} {balance['currency']}")
        
        # Тестируем получение транзакций по дате
        print("\n📅 Тестируем транзакции по дате:")
        today = datetime.now().date()
        transactions = db.get_transactions_by_date(user_id, today)
        print(f"   📝 Транзакций за сегодня: {len(transactions)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    if test_database_extended():
        print("🎉 Тест расширенной БД ПРОЙДЕН!")
    else:
        print("💥 Тест расширенной БД ПРОВАЛЕН!")