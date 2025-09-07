from history_handler import *

def test_import():
    """Тест импорта модуля"""
    print("🧪 Тестируем импорт history_handler...")
    
    # Проверяем, что все функции импортировались
    functions = [
        'history_command',
        'refresh_history_callback', 
        'edit_transaction_callback',
        'delete_transaction_callback',
        'confirm_delete_callback'
    ]
    
    for func_name in functions:
        if func_name in globals():
            print(f"✅ Функция {func_name} импортирована")
        else:
            print(f"❌ Функция {func_name} НЕ найдена")
    
    print("🎉 Тест импорта завершен!")

if __name__ == "__main__":
    test_import()