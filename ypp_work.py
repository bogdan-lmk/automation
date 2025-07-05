"""
Оптимизированная автоматизация для yupp.ai с улучшенной обработкой JSON и координат

Установка:
pip install openai pillow aiohttp

Использование:
export OPENAI_API_KEY="your_key"
python yupp_automation.py
"""

import asyncio
import time
import subprocess
import base64
import json
import os
import re
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageGrab
import aiohttp
from dataclasses import dataclass

@dataclass
class BrowserAction:
    """Действие в браузере"""
    action_type: str  # click, type, scroll, navigate, wait, key
    target: str = None  # описание элемента или URL
    value: str = None  # текст для ввода
    coordinates: Tuple[int, int] = None  # координаты для клика
    description: str = ""  # описание действия

class YuppAutomation:
    """Оптимизированная автоматизация для yupp.ai"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4o"
        
        if not self.api_key:
            raise ValueError("OpenAI API ключ не найден. Установите OPENAI_API_KEY или передайте ключ.")
        
    def log(self, message: str, level: str = "INFO"):
        """Логирование с цветными иконками"""
        icons = {
            "INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", 
            "ERROR": "❌", "AI": "🤖", "ACTION": "⚡"
        }
        print(f"{icons.get(level, 'ℹ️')} {message}")
    
    async def take_screenshot(self) -> str:
        """Создание скриншота с уникальным именем"""
        try:
            screenshot = ImageGrab.grab()
            timestamp = int(time.time() * 1000)  # Более уникальное имя
            path = f"/tmp/yupp_screenshot_{timestamp}.png"
            screenshot.save(path, optimize=True, quality=85)
            self.log(f"📸 Скриншот: {path}")
            return path
        except Exception as e:
            self.log(f"Ошибка создания скриншота: {e}", "ERROR")
            return None
    
    def image_to_base64(self, image_path: str) -> str:
        """Конвертация изображения в base64 с оптимизацией"""
        try:
            # Оптимизируем размер изображения для API
            with Image.open(image_path) as img:
                # Уменьшаем до максимум 1024px по большей стороне
                img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                
                # Сохраняем во временный файл
                temp_path = image_path.replace('.png', '_optimized.png')
                img.save(temp_path, optimize=True, quality=85)
                
                # Конвертируем в base64
                with open(temp_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode('utf-8')
                
                # Удаляем временный файл
                os.remove(temp_path)
                return encoded
                
        except Exception as e:
            self.log(f"Ошибка конвертации изображения: {e}", "ERROR")
            return None
    
    def parse_json_response(self, content: str) -> dict:
        """Улучшенный парсинг JSON ответов от AI"""
        try:
            # Ищем JSON блок
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                raise ValueError("JSON блок не найден")
            
            json_str = content[json_start:json_end]
            
            # Очищаем от частых проблем
            json_str = re.sub(r'\.{3,}', '', json_str)  # Убираем многоточия
            json_str = re.sub(r',\s*}', '}', json_str)  # Убираем лишние запятые
            json_str = re.sub(r',\s*]', ']', json_str)  # Убираем лишние запятые в массивах
            
            # Пытаемся парсить
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Если не получилось, ищем только массив actions
                actions_match = re.search(r'"actions"\s*:\s*(\[.*?\])', json_str, re.DOTALL)
                if actions_match:
                    actions_json = actions_match.group(1)
                    actions = json.loads(actions_json)
                    return {"actions": actions}
                else:
                    raise ValueError("Не удалось извлечь actions")
                    
        except Exception as e:
            self.log(f"Ошибка парсинга JSON: {e}", "ERROR")
            return None
    
    async def analyze_screen(self, command: str, screenshot_path: str) -> List[BrowserAction]:
        """Анализ скриншота и создание плана действий"""
        try:
            image_base64 = self.image_to_base64(screenshot_path)
            if not image_base64:
                return self.get_fallback_actions(command)
            
            # Улучшенный системный промпт с фокусом на кнопки prefer
            system_prompt = """You are an expert browser automation AI for yupp.ai website. 

ANALYZE the screenshot carefully and create precise actions for the user's command.

AVAILABLE ACTIONS:
1. click - Click element (MUST provide exact [x, y] coordinates)
2. type - Type text into input field
3. key - Press key (Return, Tab, Delete, etc.)
4. navigate - Go to URL
5. wait - Wait specified seconds
6. scroll - Scroll page (up/down)

SPECIAL FOCUS FOR YUPP.AI:
- Input field: Usually in bottom center (around y=700-800)
- "I prefer this" buttons: Look for small buttons below AI responses
- AI responses appear in chat bubbles with preference buttons below
- Preference buttons are often labeled "I prefer this" or have thumbs up icons
- Look carefully for clickable elements near AI response text

RESPONSE FORMAT (valid JSON only):
{
    "actions": [
        {
            "action_type": "click",
            "coordinates": [x, y],
            "description": "Click on specific element"
        },
        {
            "action_type": "type",
            "value": "text to type",
            "description": "Type specific text"
        }
    ]
}

CRITICAL RULES:
- ALWAYS provide exact coordinates [x, y] for click actions
- For "prefer" commands: scan ENTIRE screen for preference buttons
- Look for buttons, links, or clickable text related to preferences
- If multiple options exist, choose the most visible one
- Be extra careful with preference button coordinates
- Return ONLY valid JSON, no explanations outside JSON"""

            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Command: '{command}'\n\nAnalyze this yupp.ai screenshot and create action plan with EXACT coordinates:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                        }
                    ]
                }
            ]
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 800,
                "temperature": 0.1
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        
                        self.log(f"AI ответ получен ({len(content)} символов)", "AI")
                        
                        # Парсим JSON
                        plan_data = self.parse_json_response(content)
                        if not plan_data:
                            return self.get_fallback_actions(command)
                        
                        # Создаем действия
                        actions = []
                        for action_data in plan_data.get("actions", []):
                            # Исправляем поля
                            if "duration" in action_data:
                                action_data["value"] = str(action_data["duration"])
                            
                            action = BrowserAction(
                                action_type=action_data.get("action_type"),
                                target=action_data.get("target"),
                                value=action_data.get("value"),
                                coordinates=tuple(action_data.get("coordinates", [])) if action_data.get("coordinates") else None,
                                description=action_data.get("description", "")
                            )
                            actions.append(action)
                        
                        self.log(f"Создано {len(actions)} действий", "SUCCESS")
                        return actions
                    
                    else:
                        error_text = await response.text()
                        self.log(f"API ошибка {response.status}: {error_text[:200]}", "ERROR")
                        return self.get_fallback_actions(command)
        
        except Exception as e:
            self.log(f"Ошибка анализа: {e}", "ERROR")
            return self.get_fallback_actions(command)
    
    def get_fallback_actions(self, command: str) -> List[BrowserAction]:
        """Резервные действия на основе текстового анализа"""
        actions = []
        cmd = command.lower()
        
        if 'открой' in cmd and 'yupp' in cmd:
            actions.append(BrowserAction(
                action_type="navigate",
                value="https://yupp.ai",
                description="Открыть yupp.ai"
            ))
        
        elif 'подожди' in cmd:
            wait_time = 3
            numbers = re.findall(r'\d+', command)
            if numbers:
                wait_time = int(numbers[0])
            
            actions.append(BrowserAction(
                action_type="wait",
                value=str(wait_time),
                description=f"Подождать {wait_time} секунд"
            ))
        
        elif 'напиши' in cmd or 'введи' in cmd:
            # Извлекаем текст в кавычках
            text_match = re.search(r"'([^']*)'|\"([^\"]*)\"", command)
            if text_match:
                text = text_match.group(1) or text_match.group(2)
                
                # Кликаем в нижнюю часть экрана (поле ввода yupp.ai)
                actions.append(BrowserAction(
                    action_type="click",
                    coordinates=(640, 750),  # Ниже для yupp.ai
                    description="Клик в поле ввода"
                ))
                
                # Очищаем поле
                actions.append(BrowserAction(
                    action_type="key",
                    value="Command+A",
                    description="Выделить все"
                ))
                
                # Вводим текст
                actions.append(BrowserAction(
                    action_type="type",
                    value=text,
                    description=f"Ввести: {text}"
                ))
                
                # Отправляем если нужно
                if 'отправ' in cmd or 'enter' in cmd:
                    actions.append(BrowserAction(
                        action_type="key",
                        value="Return",
                        description="Отправить сообщение"
                    ))
        
        elif 'prefer' in cmd or 'кнопк' in cmd:
            # Множественные попытки клика по разным возможным позициям кнопки prefer
            prefer_positions = [
                (200, 400),   # Левая часть, средняя высота
                (200, 500),   # Левая часть, ниже
                (200, 600),   # Левая часть, еще ниже
                (400, 400),   # Центр левее
                (400, 500),   # Центр
                (400, 600),   # Центр ниже
                (600, 400),   # Правая часть
                (600, 500),   # Правая часть ниже
                (640, 400),   # Центр экрана
                (640, 500),   # Центр экрана ниже
                (800, 400),   # Дальше вправо
                (800, 500),   # Дальше вправо ниже
            ]
            
            # Пробуем первую позицию как основную
            actions.append(BrowserAction(
                action_type="click",
                coordinates=prefer_positions[0],
                description="Нажать кнопку prefer (попытка 1)"
            ))
            
            # Если команда содержит "найди", добавляем дополнительные попытки
            if 'найди' in cmd:
                for i, pos in enumerate(prefer_positions[1:4]):  # Еще 3 попытки
                    actions.append(BrowserAction(
                        action_type="wait",
                        value="1",
                        description="Короткая пауза"
                    ))
                    actions.append(BrowserAction(
                        action_type="click",
                        coordinates=pos,
                        description=f"Нажать кнопку prefer (попытка {i+2})"
                    ))
        
        elif 'enter' in cmd:
            actions.append(BrowserAction(
                action_type="key",
                value="Return",
                description="Нажать Enter"
            ))
        
        return actions
    
    async def execute_action(self, action: BrowserAction) -> bool:
        """Выполнение одного действия"""
        try:
            self.log(f"Выполнение: {action.description}", "ACTION")
            
            if action.action_type == "click":
                return await self.click(action)
            elif action.action_type == "type":
                return await self.type_text(action)
            elif action.action_type == "key":
                return await self.press_key(action)
            elif action.action_type == "navigate":
                return await self.navigate(action)
            elif action.action_type == "wait":
                return await self.wait(action)
            elif action.action_type == "scroll":
                return await self.scroll(action)
            else:
                self.log(f"Неизвестное действие: {action.action_type}", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Ошибка выполнения действия: {e}", "ERROR")
            return False
    
    async def click(self, action: BrowserAction) -> bool:
        """Клик по координатам"""
        if not action.coordinates:
            self.log("Координаты не указаны для клика", "WARNING")
            return False
        
        try:
            # Активируем браузер
            subprocess.run(['osascript', '-e', '''
                tell application "SunBrowser" to activate
            '''])
            await asyncio.sleep(0.3)
            
            x, y = action.coordinates
            
            # Выполняем клик
            subprocess.run(['osascript', '-e', f'''
                tell application "System Events"
                    click at {{{x}, {y}}}
                end tell
            '''])
            
            self.log(f"Клик по ({x}, {y})", "SUCCESS")
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            self.log(f"Ошибка клика: {e}", "ERROR")
            return False
    
    async def type_text(self, action: BrowserAction) -> bool:
        """Ввод текста"""
        if not action.value:
            self.log("Нет текста для ввода", "WARNING")
            return False
        
        try:
            # Экранируем специальные символы
            safe_text = action.value.replace('\\', '\\\\').replace('"', '\\"')
            
            subprocess.run(['osascript', '-e', f'''
                tell application "SunBrowser" to activate
                delay 0.2
                tell application "System Events"
                    keystroke "{safe_text}"
                end tell
            '''])
            
            self.log(f"Введен текст: {action.value[:50]}{'...' if len(action.value) > 50 else ''}", "SUCCESS")
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            self.log(f"Ошибка ввода текста: {e}", "ERROR")
            return False
    
    async def press_key(self, action: BrowserAction) -> bool:
        """Нажатие клавиши"""
        key = action.value or "Return"
        
        try:
            # Обработка специальных сочетаний
            if "Command" in key and "A" in key:
                script = '''
                    tell application "SunBrowser" to activate
                    delay 0.2
                    tell application "System Events"
                        keystroke "a" using {command down}
                    end tell
                '''
            elif key in ["Return", "Enter"]:
                script = '''
                    tell application "SunBrowser" to activate
                    delay 0.2
                    tell application "System Events"
                        key code 36
                    end tell
                '''
            elif key == "Delete":
                script = '''
                    tell application "SunBrowser" to activate
                    delay 0.2
                    tell application "System Events"
                        key code 51
                    end tell
                '''
            else:
                script = f'''
                    tell application "SunBrowser" to activate
                    delay 0.2
                    tell application "System Events"
                        keystroke "{key.lower()}"
                    end tell
                '''
            
            subprocess.run(['osascript', '-e', script])
            self.log(f"Нажата клавиша: {key}", "SUCCESS")
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            self.log(f"Ошибка нажатия клавиши: {e}", "ERROR")
            return False
    
    async def navigate(self, action: BrowserAction) -> bool:
        """Навигация по URL"""
        url = action.value or action.target
        if not url:
            return False
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            subprocess.run(['osascript', '-e', f'''
                tell application "SunBrowser"
                    activate
                end tell
                delay 0.5
                tell application "System Events"
                    keystroke "l" using {{command down}}
                    delay 0.3
                    keystroke "{url}"
                    delay 0.3
                    key code 36
                end tell
            '''])
            
            self.log(f"Переход на: {url}", "SUCCESS")
            await asyncio.sleep(3)  # Ждем загрузки
            return True
            
        except Exception as e:
            self.log(f"Ошибка навигации: {e}", "ERROR")
            return False
    
    async def wait(self, action: BrowserAction) -> bool:
        """Ожидание"""
        try:
            wait_time = int(action.value) if action.value else 3
            self.log(f"Ожидание {wait_time} секунд...")
            await asyncio.sleep(wait_time)
            return True
        except:
            await asyncio.sleep(3)
            return True
    
    async def scroll(self, action: BrowserAction) -> bool:
        """Прокрутка страницы"""
        direction = action.value or "down"
        
        try:
            key_code = "125" if direction == "down" else "126"  # Стрелка вниз/вверх
            
            subprocess.run(['osascript', '-e', f'''
                tell application "SunBrowser" to activate
                delay 0.2
                tell application "System Events"
                    key code {key_code}
                end tell
            '''])
            
            self.log(f"Прокрутка: {direction}", "SUCCESS")
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            self.log(f"Ошибка прокрутки: {e}", "ERROR")
            return False
    
    async def execute_command(self, command: str) -> bool:
        """Выполнение команды"""
        self.log(f"Команда: '{command}'", "INFO")
        
        # Делаем скриншот
        screenshot_path = await self.take_screenshot()
        if not screenshot_path:
            return False
        
        try:
            # Анализируем и планируем
            actions = await self.analyze_screen(command, screenshot_path)
            
            if not actions:
                self.log("Не удалось создать план действий", "ERROR")
                return False
            
            # Выполняем действия
            success_count = 0
            for i, action in enumerate(actions):
                self.log(f"Действие {i+1}/{len(actions)}: {action.description}")
                
                if await self.execute_action(action):
                    success_count += 1
                    await asyncio.sleep(0.8)  # Пауза между действиями
                else:
                    self.log(f"Действие {i+1} не выполнено", "WARNING")
            
            result = success_count > 0
            self.log(f"Результат: {success_count}/{len(actions)} действий выполнено", 
                    "SUCCESS" if result else "ERROR")
            return result
            
        finally:
            # Удаляем скриншот
            try:
                os.remove(screenshot_path)
            except:
                pass
    
    async def run_script(self, commands: List[str]) -> bool:
        """Выполнение списка команд"""
        self.log(f"Запуск скрипта из {len(commands)} команд")
        print("=" * 60)
        
        success_count = 0
        
        for i, command in enumerate(commands):
            self.log(f"Команда {i+1}/{len(commands)}: '{command}'")
            
            if await self.execute_command(command):
                success_count += 1
                if i < len(commands) - 1:  # Не ждем после последней команды
                    await asyncio.sleep(1.5)
            else:
                self.log(f"Команда {i+1} завершилась с ошибками", "WARNING")
        
        print("=" * 60)
        result = success_count == len(commands)
        self.log(f"Итог: {success_count}/{len(commands)} команд выполнено успешно", 
                "SUCCESS" if result else "WARNING")
        
        return result


async def main():
    """Главная функция"""
    print("🤖 Оптимизированная автоматизация Yupp.ai")
    print("=" * 50)
    
    # Получаем API ключ
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = input("Введите OpenAI API ключ: ").strip()
        if not api_key:
            print("❌ API ключ обязателен")
            return
    
    try:
        # Создаем автоматизацию
        automation = YuppAutomation(api_key)
        
        # Выбираем режим
        print("\n🎯 Режимы работы:")
        print("1. Интерактивный (команды по одной)")
        print("2. Скрипт (набор команд)")
        
        mode = input("Выбор (1/2): ").strip()
        
        if mode == "1":
            # Интерактивный режим
            print("\n💡 Примеры команд:")
            print("   - 'Открой yupp.ai'")
            print("   - 'Напиши Hello и отправь'")
            print("   - 'Нажми кнопку I prefer this'")
            print("   - 'Подожди 5 секунд'")
            print("💡 Для выхода: 'exit'")
            print("-" * 50)
            
            while True:
                try:
                    command = input("\n🤖 Команда: ").strip()
                    
                    if command.lower() in ['exit', 'quit', 'выход']:
                        break
                    
                    if not command:
                        continue
                    
                    await automation.execute_command(command)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    automation.log(f"Ошибка: {e}", "ERROR")
        
        elif mode == "2":
            # Режим скрипта
            yupp_commands = [
                "Открой страницу yupp.ai",
                "Подожди 4 секунды пока страница загрузится",
                "Напиши 'Что такое машинное обучение?' и отправь",
                "Нажми Enter чтобы отправить сообщение",
                "Подожди 22 секунд пока AI ответит",
                "Найди и нажми кнопку 'I prefer this'",
                "Подожди 22 секунд для получения ответа",
                "Снова нажми кнопку 'I prefer this'"
            ]
            
            print(f"\n📝 Готовый скрипт ({len(yupp_commands)} команд):")
            for i, cmd in enumerate(yupp_commands):
                print(f"   {i+1}. {cmd}")
            
            use_default = input("\nИспользовать готовый скрипт? (Y/n): ").lower().strip()
            
            if use_default != 'n':
                commands = yupp_commands
            else:
                # Пользовательский скрипт
                commands = []
                print("\n📝 Введите команды (пустая строка для завершения):")
                i = 1
                while True:
                    cmd = input(f"Команда {i}: ").strip()
                    if not cmd:
                        break
                    commands.append(cmd)
                    i += 1
            
            if commands:
                await automation.run_script(commands)
            else:
                print("⚠️ Команды не введены")
        
        else:
            print("❌ Неверный выбор")
    
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    
    print("\n👋 Завершение работы")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Остановлено пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("\n💡 Убедитесь что установлены зависимости:")
        print("pip install openai pillow aiohttp")