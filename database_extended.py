import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class FinanceDatabase:
    def __init__(self, db_path: str = "finance_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    initial_setup_completed BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Таблица транзакций
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'KZT',
                    category TEXT NOT NULL,
                    description TEXT,
                    bank TEXT,
                    transaction_type TEXT CHECK(transaction_type IN ('income', 'expense', 'transfer')) DEFAULT 'expense',
                    confidence REAL DEFAULT 1.0,
                    raw_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    transaction_date DATE DEFAULT (date('now')),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Таблица балансов счетов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS account_balances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    account_name TEXT NOT NULL,
                    account_type TEXT DEFAULT 'card',
                    balance REAL DEFAULT 0,
                    currency TEXT DEFAULT 'KZT',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, account_name)
                )
            """)
            
            conn.commit()
            print("✅ База данных инициализирована")

    def get_user_transactions_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получить историю транзакций пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, amount, currency, category, description, bank, 
                       transaction_type, transaction_date, created_at
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (user_id, limit))
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append({
                    'id': row[0],
                    'amount': row[1],
                    'currency': row[2],
                    'category': row[3],
                    'description': row[4],
                    'bank': row[5],
                    'type': row[6],
                    'date': row[7],
                    'created_at': row[8]
                })
            
            return transactions

    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Добавляет нового пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            """, (user_id, username, first_name))
            conn.commit()

    def add_transaction(self, transaction_data: Dict) -> bool:
        """Добавляет новую транзакцию"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO transactions 
                    (user_id, amount, currency, category, description, bank, 
                     transaction_type, confidence, raw_message, transaction_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction_data['user_id'],
                    transaction_data['amount'],
                    transaction_data.get('currency', 'KZT'),
                    transaction_data['category'],
                    transaction_data.get('description', ''),
                    transaction_data.get('bank'),
                    transaction_data.get('type', 'expense'),
                    transaction_data.get('confidence', 1.0),
                    transaction_data.get('raw_message', ''),
                    transaction_data.get('date', datetime.now().date())
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ Ошибка добавления транзакции: {e}")
            return False

    def get_transaction_by_id(self, transaction_id: int, user_id: int) -> Optional[Dict]:
        """Получить транзакцию по ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, amount, currency, category, description, bank, 
                       transaction_type, transaction_date, created_at
                FROM transactions 
                WHERE id = ? AND user_id = ?
            """, (transaction_id, user_id))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'amount': row[1],
                    'currency': row[2],
                    'category': row[3],
                    'description': row[4],
                    'bank': row[5],
                    'type': row[6],
                    'date': row[7],
                    'created_at': row[8]
                }
            return None

    def delete_transaction(self, transaction_id: int, user_id: int) -> bool:
        """Удалить транзакцию"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM transactions 
                    WHERE id = ? AND user_id = ?
                """, (transaction_id, user_id))
                conn.commit()
                
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Ошибка удаления транзакции: {e}")
            return False

    def get_user_statistics(self, user_id: int, period_days: int = 30) -> Dict:
        """Получить статистику пользователя за период"""
        start_date = (datetime.now() - timedelta(days=period_days)).date()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Статистика по категориям
            cursor.execute("""
                SELECT category, SUM(amount) as total, COUNT(*) as count
                FROM transactions 
                WHERE user_id = ? AND transaction_date >= ? AND transaction_type = 'expense'
                GROUP BY category
                ORDER BY total DESC
            """, (user_id, start_date))
            
            expenses_by_category = []
            total_expenses = 0
            for row in cursor.fetchall():
                amount = row[1]
                expenses_by_category.append({
                    'category': row[0],
                    'amount': amount,
                    'count': row[2]
                })
                total_expenses += amount
            
            # Доходы
            cursor.execute("""
                SELECT SUM(amount) 
                FROM transactions 
                WHERE user_id = ? AND transaction_date >= ? AND transaction_type = 'income'
            """, (user_id, start_date))
            
            total_income = cursor.fetchone()[0] or 0
            
            return {
                'expenses_by_category': expenses_by_category,
                'total_expenses': total_expenses,
                'total_income': total_income,
                'period_days': period_days
            }

    def get_transactions_by_date(self, user_id: int, date) -> List[Dict]:
        """Получить транзакции за конкретную дату"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, amount, currency, category, description, bank, 
                       transaction_type, transaction_date, created_at
                FROM transactions 
                WHERE user_id = ? AND DATE(transaction_date) = DATE(?)
                ORDER BY created_at DESC
            """, (user_id, date))
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append({
                    'id': row[0],
                    'amount': row[1],
                    'currency': row[2],
                    'category': row[3],
                    'description': row[4],
                    'bank': row[5],
                    'type': row[6],
                    'date': row[7],
                    'created_at': row[8]
                })
            
            return transactions

    def add_transfer(self, user_id: int, amount: float, from_account: str, 
                     to_account: str, description: str = "", raw_message: str = "") -> bool:
        """Добавить перевод между счетами"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Добавляем запись о переводе
                cursor.execute("""
                    INSERT INTO transactions 
                    (user_id, amount, currency, category, description, bank, 
                     transaction_type, confidence, raw_message, transaction_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    amount,
                    'KZT',
                    'перевод',
                    description or f"Перевод с {from_account} на {to_account}",
                    f"{from_account} → {to_account}",
                    'transfer',
                    1.0,
                    raw_message,
                    datetime.now().date()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ Ошибка добавления перевода: {e}")
            return False

    def update_account_balance(self, user_id: int, account_name: str, amount_change: float) -> bool:
        """Обновить баланс счета"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Получаем текущий баланс
                cursor.execute("""
                    SELECT balance FROM account_balances 
                    WHERE user_id = ? AND account_name = ?
                """, (user_id, account_name))
                
                result = cursor.fetchone()
                if result:
                    # Обновляем существующий баланс
                    new_balance = result[0] + amount_change
                    cursor.execute("""
                        UPDATE account_balances 
                        SET balance = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND account_name = ?
                    """, (new_balance, user_id, account_name))
                else:
                    # Создаем новый счет с начальным балансом
                    cursor.execute("""
                        INSERT INTO account_balances 
                        (user_id, account_name, balance, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """, (user_id, account_name, amount_change))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Ошибка обновления баланса: {e}")
            return False

    def get_account_balances(self, user_id: int) -> List[Dict]:
        """Получить все балансы счетов пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT account_name, account_type, balance, currency, updated_at
                FROM account_balances 
                WHERE user_id = ?
                ORDER BY account_name
            """, (user_id,))
            
            balances = []
            for row in cursor.fetchall():
                balances.append({
                    'account_name': row[0],
                    'account_type': row[1],
                    'balance': row[2],
                    'currency': row[3],
                    'updated_at': row[4]
                })
            
            return balances

    def add_account_balance(self, user_id: int, account_name: str, balance: float, 
                           account_type: str = 'card') -> bool:
        """Добавить или обновить баланс счета"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO account_balances 
                    (user_id, account_name, account_type, balance, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, account_name, account_type, balance))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Ошибка добавления баланса: {e}")
            return False

# Создаем экземпляр базы данных
db = FinanceDatabase()