def test_statistics_import():
    """Тест импорта модуля статистики"""
    print("🧪 Тестируем statistics_handler...")
    
    try:
        from statistics_handler import (
            statistics_command,
            show_daily_statistics,
            create_date_navigation_keyboard,
            stats_day_callback,
            stats_month_callback
        )
        print("✅ Все функции статистики импортированы")
        
        # Тестируем создание клавиатуры навигации
        from datetime import datetime
        today = datetime.now().date()
        keyboard = create_date_navigation_keyboard(today)
        
        print(f"✅ Клавиатура навигации создана: {len(keyboard)} рядов кнопок")
        print(f"   Кнопки дней: {len(keyboard[0])} кнопок")
        print(f"   Кнопки месяцев: {len(keyboard[1])} кнопок")
        print(f"   Кнопки фильтров: {len(keyboard[2])} кнопок")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    if test_statistics_import():
        print("🎉 Тест statistics_handler ПРОЙДЕН!")
    else:
        print("💥 Тест statistics_handler ПРОВАЛЕН!")