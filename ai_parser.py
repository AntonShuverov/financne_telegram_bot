import openai
import json
import os
from dotenv import load_dotenv
from typing import Dict, Optional

load_dotenv()

class AIParser:
    def __init__(self):
        """Инициализация ИИ парсера"""
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # Стандартные категории
        self.categories = {
            "expense": ["еда", "транспорт", "развлечения", "покупки", "жилье", "здоровье", "другое"],
            "income": ["зарплата", "инвестиции", "подарки", "подработка", "другое"]
        }
        
        # Стандартные банки
        self.banks = ["kaspi", "halyk", "sber", "forte", "наличные", "другое"]
    
    def parse_transaction(self, message: str) -> Dict:
        """Парсинг сообщения о финансовой операции"""
        
        prompt = f"""Извлеки из сообщения информацию о финансовой операции.

Сообщение: "{message}"

Определи и верни JSON в точном формате:
{{
  "amount": число без валюты или null если не найдено,
  "currency": "KZT" или "RUB" или "USD" или "EUR" или null,
  "category": одна из категорий: {', '.join(self.categories['expense'] + self.categories['income'])},
  "description": "краткое описание на русском",
  "bank": одна из: {', '.join(self.banks)} или null,
  "type": "expense" или "income",
  "confidence": число от 0 до 1
}}

Правила:
- Если сумма не найдена, amount = null
- Для зарплаты, премии, подарков, инвестиций type = "income"
- Для покупок, трат, оплаты type = "expense"  
- currency по умолчанию "KZT" если не указана другая
- confidence = 1 если полностью уверен, 0.5-0.8 если есть сомнения
- description должно быть коротким и понятным

Примеры:
- "потратил 2500 на кофе" → {{"amount": 2500, "currency": "KZT", "category": "еда", "description": "кофе", "bank": null, "type": "expense", "confidence": 0.9}}
- "получил зарплату 400000" → {{"amount": 400000, "currency": "KZT", "category": "зарплата", "description": "зарплата", "bank": null, "type": "income", "confidence": 1.0}}
"""

        try:
            response = openai.Completion.create(
                engine="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=200,
                temperature=0.1,
                stop=None
            )
            
            result_text = response.choices[0].text.strip()
            
            # Пытаемся извлечь JSON из ответа
            if '{' in result_text and '}' in result_text:
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                json_text = result_text[json_start:json_end]
                
                parsed_data = json.loads(json_text)
                
                # Валидация данных
                validated_data = self._validate_parsed_data(parsed_data)
                return validated_data
            else:
                return self._create_error_response("Не удалось извлечь JSON из ответа ИИ")
                
        except json.JSONDecodeError as e:
            return self._create_error_response(f"Ошибка парсинга JSON: {str(e)}")
        except Exception as e:
            return self._create_error_response(f"Ошибка ИИ: {str(e)}")
    
    def _validate_parsed_data(self, data: Dict) -> Dict:
        """Валидация и очистка данных от ИИ"""
        validated = {
            "amount": data.get("amount"),
            "currency": data.get("currency", "KZT"),
            "category": data.get("category", "другое"),
            "description": data.get("description", ""),
            "bank": data.get("bank"),
            "type": data.get("type", "expense"),
            "confidence": float(data.get("confidence", 0.5)),
            "success": True,
            "error": None
        }
        
        # Проверяем валидность категории
        all_categories = self.categories["expense"] + self.categories["income"]
        if validated["category"] not in all_categories:
            validated["category"] = "другое"
            validated["confidence"] *= 0.8
        
        # Проверяем тип транзакции
        if validated["type"] not in ["expense", "income"]:
            validated["type"] = "expense"
        
        # Проверяем сумму
        if validated["amount"] is not None:
            try:
                validated["amount"] = float(validated["amount"])
                if validated["amount"] <= 0:
                    validated["amount"] = None
            except (ValueError, TypeError):
                validated["amount"] = None
        
        return validated
    
    def _create_error_response(self, error_msg: str) -> Dict:
        """Создание ответа об ошибке"""
        return {
            "amount": None,
            "currency": "KZT",
            "category": "другое",
            "description": "",
            "bank": None,
            "type": "expense",
            "confidence": 0.0,
            "success": False,
            "error": error_msg
        }
    
    def suggest_new_category(self, message: str) -> Optional[Dict]:
        """Предложение новой категории если стандартные не подходят"""
        
        prompt = f"""Пользователь написал: "{message}"

Стандартные категории: {', '.join(self.categories['expense'] + self.categories['income'])}

Если трата не подходит ни в одну стандартную категорию, предложи новую:

Формат ответа JSON:
{{
  "create_new": true/false,
  "category_name": "название новой категории",
  "emoji": "подходящий эмодзи",
  "type": "expense" или "income",
  "confidence": число от 0 до 1
}}

Если подходит стандартная категория, верни {{"create_new": false}}
"""

        try:
            response = openai.Completion.create(
                engine="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=100,
                temperature=0.2
            )
            
            result_text = response.choices[0].text.strip()
            
            if '{' in result_text and '}' in result_text:
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                json_text = result_text[json_start:json_end]
                
                return json.loads(json_text)
            
        except Exception as e:
            print(f"Ошибка при предложении категории: {e}")
        
        return {"create_new": False}

# Создаем глобальный экземпляр парсера
ai_parser = AIParser()