import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class FinanceDatabase:
    def __init__(self, db_path: str = "finance.db"):
        """Инициализация базы данных"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Создание таблиц если их нет"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    timezone TEXT DEFAULT 'Asia/Almaty',
                    currency TEXT DEFAULT 'KZT',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица транзакций
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date DATETIME,
                    amount REAL,
                    currency TEXT,
                    category TEXT,
                    description TEXT,
                    bank TEXT,
                    type TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица категорий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    emoji TEXT,
                    type TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица целей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    target_amount REAL,
                    current_amount REAL DEFAULT 0,
                    currency TEXT,
                    target_date DATE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица лимитов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT,
                    monthly_limit REAL,
                    currency TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
        print("✅ База данных инициализирована")
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Добавление нового пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            conn.commit()
    
    def add_transaction(self, user_id: int, amount: float, currency: str, 
                       category: str, description: str, bank: str = None, 
                       transaction_type: str = "expense"):
        """Добавление новой транзакции"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, date, amount, currency, category, description, bank, type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, datetime.now(), amount, currency, category, description, bank, transaction_type))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_transactions(self, user_id: int, month: int = None, year: int = None) -> List[Dict]:
        """Получение транзакций пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if month and year:
                cursor.execute('''
                    SELECT * FROM transactions 
                    WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
                    ORDER BY date DESC
                ''', (user_id, f"{month:02d}", str(year)))
            else:
                cursor.execute('''
                    SELECT * FROM transactions 
                    WHERE user_id = ?
                    ORDER BY date DESC
                ''', (user_id,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_category_stats(self, user_id: int, month: int, year: int, transaction_type: str = "expense") -> List[Dict]:
        """Статистика по категориям"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, SUM(amount) as total, COUNT(*) as count
                FROM transactions 
                WHERE user_id = ? AND type = ? 
                AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
                GROUP BY category
                ORDER BY total DESC
            ''', (user_id, transaction_type, f"{month:02d}", str(year)))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def add_default_categories(self, user_id: int):
        """Добавление стандартных категорий для нового пользователя"""
        default_categories = [
            # Расходы
            ("еда", "🍕", "expense"),
            ("транспорт", "🚗", "expense"),
            ("развлечения", "🎮", "expense"),
            ("покупки", "🛒", "expense"),
            ("жилье", "🏠", "expense"),
            ("здоровье", "💊", "expense"),
            # Доходы
            ("зарплата", "💼", "income"),
            ("инвестиции", "📈", "income"),
            ("подарки", "🎁", "income"),
            ("подработка", "💰", "income"),
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for name, emoji, cat_type in default_categories:
                cursor.execute('''
                    INSERT OR IGNORE INTO categories (user_id, name, emoji, type)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, name, emoji, cat_type))
            conn.commit()
    
    def close(self):
        """Закрытие соединения (если потребуется)"""
        pass

# Создаем глобальный экземпляр базы данных
db = FinanceDatabase()