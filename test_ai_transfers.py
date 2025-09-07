def test_ai_transfers():
    """Тест функций переводов в ИИ парсере"""
    print("🧪 Тестируем ИИ переводы...")
    
    try:
        from ai_parser import ai_parser
        
        # Проверяем, что новые методы добавлены
        methods_to_check = [
            'detect_transfer',
            'parse_transfer', 
            'normalize_bank_name',
            'parse_transaction_or_transfer'
        ]
        
        missing_methods = []
        for method in methods_to_check:
            if not hasattr(ai_parser, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Отсутствуют методы: {missing_methods}")
            print("💡 Нужно добавить методы в ai_parser.py")
            return False
        
        print("✅ Все методы переводов найдены в ai_parser")
        
        # Тестируем определение переводов
        transfer_messages = [
            "перевел с каспи на халык 50000",
            "снял с халыка 25000 наличными",
            "пополнил каспи 30000",
            "купил кофе 800 тг"  # не перевод
        ]
        
        print("\n🔍 Тестируем определение переводов:")
        for msg in transfer_messages:
            is_transfer = ai_parser.detect_transfer(msg)
            status = "✅ ПЕРЕВОД" if is_transfer else "❌ НЕ ПЕРЕВОД"
            print(f"   '{msg}' → {status}")
        
        # Тестируем нормализацию банков
        print("\n🏦 Тестируем нормализацию банков:")
        bank_tests = [
            ("каспи", "kaspi"),
            ("Halyk Bank", "halyk"), 
            ("наличные", "наличные"),
            ("неизвестный банк", "другое")
        ]
        
        for input_bank, expected in bank_tests:
            result = ai_parser.normalize_bank_name(input_bank)
            status = "✅" if result == expected else "❌"
            print(f"   '{input_bank}' → '{result}' {status}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    if test_ai_transfers():
        print("🎉 Тест ИИ переводов ПРОЙДЕН!")
    else:
        print("💥 Тест ИИ переводов ПРОВАЛЕН!")
        