import pyautogui
import time
import subprocess
import psutil
import platform
import os
from typing import Optional, Dict, List, Tuple

class BrowserAutomation:
    """Универсальный класс для автоматизации браузера"""
    
    def __init__(self, config: Dict = None):
        """
        Инициализация с конфигурацией
        
        Args:
            config: Словарь с настройками автоматизации
        """
        # Дефолтная конфигурация
        self.default_config = {
            # Настройки поиска браузера
            "browser": {
                "process_names": ["sunbrowser"],
                "window_titles": ["sunbrowser"]
            },
            
            # Настройки экрана и безопасности
            "screen": {
                "margin_from_edges": 50,
                "click_duration": 0.5,
                "move_duration": 0.3,
                "step_delay": 2
            },
            
            # Настройки поиска элементов
            "search": {
                "confidence_levels": [0.9, 0.8, 0.7, 0.6, 0.5],
                "timeout": 30,
                "retry_delay": 1
            },
            
            # Шаги автоматизации (последовательность действий)
            "steps": [
                {
                    "name": "find_browser",
                    "type": "browser_detection",
                    "description": "Поиск и активация браузера"
                },
                {
                    "name": "click_signin_button", 
                    "type": "screenshot_click",
                    "screenshot_path": "screenshots/ypp/btn1.png",
                    "fallback_coords": {"x_ratio": 0.5, "y_ratio": 0.75},
                    "description": "Клик по кнопке входа"
                },
                {
                    "name": "click_account",
                    "type": "coordinate_click", 
                    "coords": {"x_ratio": 0.75, "y_ratio": 0.5},
                    "description": "Клик по аккаунту"
                }
            ]
        }
        
        # Объединяем переданную конфигурацию с дефолтной
        self.config = self._merge_configs(self.default_config, config or {})
        
        # Настройки pyautogui
        self.original_failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False
    
    def _merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """Рекурсивное объединение конфигураций"""
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def log(self, message: str, level: str = "INFO"):
        """Универсальная функция логирования"""
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "DEBUG": "🔍"}
        print(f"{icons.get(level, 'ℹ️')} {message}")
    
    def get_screen_info(self) -> Tuple[int, int]:
        """Получение информации об экране"""
        width, height = pyautogui.size()
        self.log(f"Размер экрана: {width}x{height}", "DEBUG")
        return width, height
    
    def coords_from_ratio(self, x_ratio: float, y_ratio: float) -> Tuple[int, int]:
        """Преобразование относительных координат в абсолютные"""
        screen_width, screen_height = self.get_screen_info()
        x = int(screen_width * x_ratio)
        y = int(screen_height * y_ratio)
        return x, y
    
    def is_coords_safe(self, x: int, y: int) -> bool:
        """Проверка безопасности координат"""
        screen_width, screen_height = self.get_screen_info()
        margin = self.config["screen"]["margin_from_edges"]
        
        return (margin <= x <= screen_width - margin and 
                margin <= y <= screen_height - margin)
    
    def safe_click(self, x: int, y: int) -> bool:
        """Безопасный клик по координатам"""
        try:
            if not self.is_coords_safe(x, y):
                self.log(f"Координаты ({x}, {y}) небезопасны, корректируем...", "WARNING")
                screen_width, screen_height = self.get_screen_info()
                margin = self.config["screen"]["margin_from_edges"]
                x = max(margin, min(x, screen_width - margin))
                y = max(margin, min(y, screen_height - margin))
                self.log(f"Скорректированные координаты: ({x}, {y})", "DEBUG")
            
            # Плавное перемещение и клик
            move_duration = self.config["screen"]["move_duration"]
            click_duration = self.config["screen"]["click_duration"]
            
            pyautogui.moveTo(x, y, duration=move_duration)
            time.sleep(0.2)
            pyautogui.click(x, y)
            
            current_pos = pyautogui.position()
            self.log(f"Клик выполнен по ({x}, {y}), текущая позиция: {current_pos}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Ошибка при клике: {e}", "ERROR")
            return False
    
    def find_browser_window(self) -> Optional[Dict]:
        """Универсальный поиск окна браузера"""
        self.log("Поиск окна браузера...")
        
        try:
            # Получаем список приложений через AppleScript (для macOS)
            applescript = '''
            tell application "System Events"
                set appList to (name of every application process whose background only is false)
            end tell
            return appList
            '''
            result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
            
            if result.returncode == 0:
                apps = result.stdout.strip().split(', ')
                self.log(f"Найдены приложения: {apps}", "DEBUG")
                
                # Ищем браузер по настроенным именам
                browser_names = self.config["browser"]["process_names"]
                found_browsers = []
                
                for app in apps:
                    for browser_name in browser_names:
                        if browser_name.lower() in app.lower():
                            found_browsers.append(app)
                            break
                
                if found_browsers:
                    self.log(f"Найдены браузеры: {found_browsers}", "SUCCESS")
                    
                    # Возвращаем информацию о первом найденном браузере
                    return {
                        'title': found_browsers[0],
                        'app_name': found_browsers[0],
                        'found': True
                    }
            
            self.log("Браузер не найден", "ERROR")
            return None
            
        except Exception as e:
            self.log(f"Ошибка поиска браузера: {e}", "ERROR")
            return None
    
    def activate_browser_window(self, window_info: Dict) -> bool:
        """Универсальная активация окна браузера"""
        try:
            app_name = window_info['app_name']
            self.log(f"Активация окна: {app_name}")
            
            activate_script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set frontmost to true
                    if (count of windows) > 0 then
                        tell window 1
                            set index to 1
                        end tell
                    end if
                end tell
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', activate_script], capture_output=True, text=True)
            
            if result.returncode == 0:
                time.sleep(1)
                self.log(f"Окно активировано: {app_name}", "SUCCESS")
                return True
            else:
                self.log(f"Ошибка активации: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Ошибка активации окна: {e}", "ERROR")
            return False
    
    def click_by_coordinates(self, coords: Dict) -> bool:
        """Клик по относительным координатам"""
        if "x_ratio" in coords and "y_ratio" in coords:
            x, y = self.coords_from_ratio(coords["x_ratio"], coords["y_ratio"])
        else:
            x, y = coords.get("x", 0), coords.get("y", 0)
        
        self.log(f"Клик по координатам: ({x}, {y})")
        return self.safe_click(x, y)
    
    def find_element_by_text(self, text: str, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """Поиск элемента по тексту на экране"""
        try:
            import pytesseract
            from PIL import Image
            
            # Делаем скриншот экрана
            screenshot = pyautogui.screenshot()
            
            # Извлекаем текст и координаты
            ocr_data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
            
            # Ищем все совпадения в центральной области экрана
            screen_width, screen_height = self.get_screen_info()
            center_matches = []
            
            for i, detected_text in enumerate(ocr_data['text']):
                if (text.lower() in detected_text.lower() and 
                    int(ocr_data['conf'][i]) > confidence * 100):
                    
                    x = ocr_data['left'][i] + ocr_data['width'][i] // 2
                    y = ocr_data['top'][i] + ocr_data['height'][i] // 2
                    
                    # Проверяем что элемент в центральной области
                    if (screen_width * 0.2 <= x <= screen_width * 0.8 and
                        screen_height * 0.3 <= y <= screen_height * 0.8):
                        center_matches.append((x, y))
                        self.log(f"Найден текст '{text}' на координатах ({x}, {y})", "DEBUG")
            
            if center_matches:
                # Берем самый центральный элемент
                center_x, center_y = screen_width // 2, screen_height // 2
                best_match = min(center_matches, 
                               key=lambda p: abs(p[0] - center_x) + abs(p[1] - center_y))
                self.log(f"Выбран наиболее центральный элемент: {best_match}", "SUCCESS")
                return best_match
            
            return None
            
        except ImportError:
            self.log("Для поиска по тексту нужно установить: pip install pytesseract", "WARNING")
            return None
        except Exception as e:
            self.log(f"Ошибка поиска по тексту: {e}", "ERROR")
            return None
    
    def find_google_button_smart(self) -> Optional[Tuple[int, int]]:
        """Умный поиск кнопки Google по различным признакам"""
        self.log("Умный поиск кнопки Google...")
        
        # 1. Пробуем найти по тексту (только точные совпадения)
        text_variations = [
            "Sign in with Google",
            "Continue with Google", 
            "Login with Google"
        ]
        
        for text in text_variations:
            coords = self.find_element_by_text(text, confidence=0.9)
            if coords:
                self.log(f"Кнопка найдена по тексту '{text}'", "SUCCESS")
                return coords
        
        # 2. Fallback: предполагаемая позиция по центру экрана
        screen_width, screen_height = self.get_screen_info()
        fallback_x = screen_width // 2
        fallback_y = int(screen_height * 0.75)  # Кнопка обычно в нижней части
        
        self.log(f"Используем предполагаемые координаты кнопки Google: ({fallback_x}, {fallback_y})", "INFO")
        return (fallback_x, fallback_y)
    
    def wait_for_page_change(self, timeout: int = 10) -> bool:
        """Ожидание изменения страницы"""
        self.log(f"Ожидание изменения страницы ({timeout}с)...")
        
        # Делаем скриншот до
        screenshot_before = pyautogui.screenshot()
        
        for i in range(timeout):
            time.sleep(1)
            screenshot_after = pyautogui.screenshot()
            
            # Сравниваем скриншоты (простое сравнение по размеру данных)
            if screenshot_before.tobytes() != screenshot_after.tobytes():
                self.log(f"Страница изменилась через {i+1}с", "SUCCESS")
                return True
            
            if i % 2 == 0:  # Каждые 2 секунды
                self.log(f"Ожидание... {i+1}/{timeout}с", "DEBUG")
        
        self.log("Страница не изменилась за отведенное время", "WARNING")
        return False
    
    def find_email_account_smart(self) -> Optional[Tuple[int, int]]:
        """Умный поиск аккаунта электронной почты"""
        self.log("Умный поиск аккаунта электронной почты...")
        
        # Ждем загрузки страницы выбора аккаунта
        self.wait_for_page_change(timeout=5)
        
        # 1. Поиск по характерным текстам для аккаунта
        account_patterns = [
            "@gmail.com",
            "gmail.com",
            "Choose an account",
            "boban marjan",
            "marjanboban01"
        ]
        
        for pattern in account_patterns:
            coords = self.find_element_by_text(pattern, confidence=0.8)
            if coords:
                self.log(f"Аккаунт найден по тексту '{pattern}'", "SUCCESS")
                return coords
        
        # 2. Поиск первого аккаунта в списке (скорректированные координаты)
        screen_width, screen_height = self.get_screen_info()
        
        # Скорректированные координаты: правее на 30px, ниже на 20px
        base_x = int(screen_width * 0.5) + 30  # Центр + 30px правее
        base_y = int(screen_height * 0.4) + 20  # 40% высоты + 20px ниже
        
        # Ищем в области аккаунта с несколькими вариантами
        search_areas = [
            (base_x, base_y),                    # Основная позиция (скорректированная)
            (base_x + 20, base_y),              # Еще правее
            (base_x, base_y + 15),              # Еще ниже
            (base_x + 40, base_y + 10),         # Правее и немного ниже
        ]
        
        for x, y in search_areas:
            self.log(f"Пробуем кликнуть по области аккаунта: ({x}, {y})", "INFO")
            return (x, y)
        
        return None
    
    def find_continue_button_smart(self) -> Optional[Tuple[int, int]]:
        """Умный поиск кнопки Продолжить"""
        self.log("Умный поиск кнопки Продолжить...")
        
        # 1. Поиск по тексту кнопки
        continue_texts = [
            "Продовжити",
            "Продолжить", 
            "Continue",
            "Далі",
            "Next"
        ]
        
        for text in continue_texts:
            coords = self.find_element_by_text(text, confidence=0.8)
            if coords:
                self.log(f"Кнопка Продолжить найдена по тексту '{text}'", "SUCCESS")
                return coords
        
        # 2. Универсальный поиск через зоны экрана
        screen_width, screen_height = self.get_screen_info()
        
        # Определяем зоны поиска для кнопки (правый нижний квадрант)
        search_zones = [
            # Зона 1: Стандартное место для кнопки Continue
            {
                "x_ratio": 0.78,   # 78% ширины экрана
                "y_ratio": 0.80,   # 80% высоты экрана
                "name": "стандартная позиция"
            },
            # Зона 2: Немного левее (по наблюдениям из координат 1119 из 1440)
            {
                "x_ratio": 0.777,  # 1119/1440 ≈ 0.777
                "y_ratio": 0.802,  # 722/900 ≈ 0.802
                "name": "точная пропорция"
            },
            # Зона 3: Альтернативные позиции
            {
                "x_ratio": 0.75,
                "y_ratio": 0.85,
                "name": "альтернативная позиция"
            },
            # Зона 4: Центрально-правая
            {
                "x_ratio": 0.8,
                "y_ratio": 0.75,
                "name": "центрально-правая"
            }
        ]
        
        # Пробуем каждую зону
        for zone in search_zones:
            x = int(screen_width * zone["x_ratio"])
            y = int(screen_height * zone["y_ratio"])
            
            self.log(f"Пробуем зону '{zone['name']}': ({x}, {y})", "DEBUG")
            
            # Можно добавить проверку цвета пикселя или другую валидацию
            if self.is_coords_safe(x, y):
                self.log(f"Используем координаты из зоны '{zone['name']}': ({x}, {y})", "INFO")
                return (x, y)
        
        # 3. Fallback: расчет от краев экрана
        margin_from_right = 100  # 100px от правого края
        margin_from_bottom = 80  # 80px от нижнего края
        
        fallback_x = screen_width - margin_from_right
        fallback_y = screen_height - margin_from_bottom
        
    def find_button_with_ai_vision(self, button_description: str = "Continue button") -> Optional[Tuple[int, int]]:
        """Поиск кнопки с помощью AI Vision (DeepSeek)"""
        try:
            import base64
            import requests
            from io import BytesIO
            
            self.log(f"AI Vision поиск: {button_description}")
            
            # Делаем скриншот
            screenshot = pyautogui.screenshot()
            
            # Конвертируем в base64
            buffer = BytesIO()
            screenshot.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Запрос к DeepSeek API
            api_key = "sk-2f6aad2a5d76478c9f4c70b48d0b2efd"  # Замените на ваш ключ
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Найди на этом скриншоте кнопку: {button_description}
                                
                                Проанализируй изображение и найди кнопку с текстом "Продолжить", "Continue", "Далі" или похожим.
                                
                                Верни ТОЛЬКО координаты в формате: x,y
                                Где x,y - это пиксельные координаты центра кнопки.
                                
                                Если кнопка не найдена, верни: NOT_FOUND"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 50
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                
                self.log(f"AI ответ: {ai_response}", "DEBUG")
                
                # Парсим координаты
                if "NOT_FOUND" not in ai_response and "," in ai_response:
                    try:
                        coords = ai_response.replace(" ", "").split(",")
                        x, y = int(coords[0]), int(coords[1])
                        
                        # Проверяем валидность координат
                        screen_width, screen_height = self.get_screen_info()
                        if 0 <= x <= screen_width and 0 <= y <= screen_height:
                            self.log(f"✅ AI нашел кнопку: ({x}, {y})", "SUCCESS")
                            return (x, y)
                        else:
                            self.log(f"⚠️ AI координаты вне экрана: ({x}, {y})", "WARNING")
                    except ValueError:
                        self.log(f"❌ Не удалось распарсить координаты: {ai_response}", "ERROR")
                
            return None
            
        except Exception as e:
            self.log(f"Ошибка AI Vision: {e}", "ERROR")
            return None
    
    def find_continue_button_ai_enhanced(self) -> Optional[Tuple[int, int]]:
        """AI-улучшенный поиск кнопки Продолжить"""
        self.log("🤖 AI-улучшенный поиск кнопки Продолжить...")
        
        # Метод 1: AI Vision (DeepSeek)
        coords = self.find_button_with_ai_vision("Continue/Продолжить button in bottom right area")
        if coords:
            return coords
        
        # Метод 2: OCR + AI анализ
        coords = self.find_button_with_smart_ai_ocr()
        if coords:
            return coords
        
        # Fallback к обычному методу
        self.log("AI не нашел кнопку, используем обычный поиск", "WARNING")
        return self.find_continue_button_smart()
    
    def find_button_with_smart_ai_ocr(self) -> Optional[Tuple[int, int]]:
        """Умный OCR + AI для поиска кнопок"""
        try:
            import pytesseract
            
            # Делаем скриншот
            screenshot = pyautogui.screenshot()
            
            # Извлекаем весь текст с координатами
            ocr_data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
            
            # Собираем все найденные тексты
            found_texts = []
            for i, text in enumerate(ocr_data['text']):
                if text.strip() and int(ocr_data['conf'][i]) > 50:
                    x = ocr_data['left'][i] + ocr_data['width'][i] // 2
                    y = ocr_data['top'][i] + ocr_data['height'][i] // 2
                    found_texts.append(f"{text}:{x},{y}")
            
            if found_texts:
                # Используем AI для анализа найденных текстов
                ai_analysis = self.analyze_texts_with_ai(found_texts)
                if ai_analysis:
                    return ai_analysis
            
            return None
            
        except ImportError:
            self.log("Для smart OCR нужно: pip install pytesseract", "WARNING")
            return None
    
    def analyze_texts_with_ai(self, texts: List[str]) -> Optional[Tuple[int, int]]:
        """Анализ найденных текстов с помощью AI"""
        try:
            import requests
            
            api_key = "YOUR_DEEPSEEK_API_KEY"  # Замените на ваш ключ
            
            texts_str = "\n".join(texts[:20])  # Берем первые 20 элементов
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": f"""Из списка найденных текстов с координатами найди кнопку "Продолжить"/"Continue"/"Далі":

{texts_str}

Формат: текст:x,y

Найди текст который означает "продолжить" или "continue" и верни его координаты в формате: x,y
Если не найдено, верни: NOT_FOUND"""
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 30
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                
                if "NOT_FOUND" not in ai_response and "," in ai_response:
                    coords = ai_response.replace(" ", "").split(",")
                    x, y = int(coords[0]), int(coords[1])
                    self.log(f"✅ AI анализ OCR нашел: ({x}, {y})", "SUCCESS")
                    return (x, y)
            
            return None
            
        except Exception as e:
            self.log(f"Ошибка AI анализа: {e}", "ERROR")
            return None
    
    def click_by_screenshot(self, screenshot_path: str, fallback_coords: Dict = None) -> bool:
        """Универсальный клик по скриншоту с fallback"""
        self.log(f"Поиск элемента по скриншоту: {screenshot_path}")
        
        if not os.path.exists(screenshot_path):
            self.log(f"Файл скриншота не найден: {screenshot_path}", "WARNING")
            if fallback_coords:
                return self.click_by_coordinates(fallback_coords)
            return False
        
        # Уменьшаем количество попыток чтобы не зависать
        max_attempts = 3
        confidence_levels = [0.8, 0.6, 0.4]
        
        for attempt in range(max_attempts):
            for confidence in confidence_levels:
                try:
                    location = pyautogui.locateCenterOnScreen(screenshot_path, confidence=confidence)
                    
                    if location:
                        self.log(f"Элемент найден: {location} (confidence={confidence})", "SUCCESS")
                        
                        if self.is_coords_safe(int(location.x), int(location.y)):
                            return self.safe_click(int(location.x), int(location.y))
                        else:
                            self.log(f"Координаты небезопасны: {location}", "WARNING")
                
                except pyautogui.ImageNotFoundException:
                    continue
                except Exception as e:
                    self.log(f"Ошибка поиска (confidence={confidence}): {e}", "DEBUG")
                    continue
            
            time.sleep(0.5)  # Уменьшили задержку
        
        self.log("Элемент не найден по скриншоту, переходим к умному поиску", "WARNING")
        
        # Используем fallback координаты если есть
        if fallback_coords:
            self.log("Используем fallback координаты", "INFO")
            return self.click_by_coordinates(fallback_coords)
        
        return False
    
    def execute_step(self, step: Dict) -> bool:
        """Выполнение одного шага автоматизации"""
        step_name = step.get("name", "unknown")
        step_type = step.get("type", "unknown")
        description = step.get("description", step_name)
        
        self.log(f"=== Выполнение шага: {description} ===")
        
        if step_type == "browser_detection":
            window_info = self.find_browser_window()
            if window_info:
                return self.activate_browser_window(window_info)
            return False
            
        elif step_type == "screenshot_click":
            screenshot_path = step.get("screenshot_path")
            fallback_coords = step.get("fallback_coords")
            return self.click_by_screenshot(screenshot_path, fallback_coords)
            
        elif step_type == "smart_google_click":
            coords = self.find_google_button_smart()
            if coords:
                return self.safe_click(coords[0], coords[1])
            return False
            
        elif step_type == "smart_email_click":
            coords = self.find_email_account_smart()
            if coords:
                return self.safe_click(coords[0], coords[1])
            return False
            
        elif step_type == "smart_continue_click":
            coords = self.find_continue_button_ai_enhanced()  # Используем AI версию
            if coords:
                return self.safe_click(coords[0], coords[1])
            return False
            
        elif step_type == "wait_for_load":
            seconds = step.get("seconds", 3)
            self.log(f"Ожидание загрузки {seconds} секунд")
            time.sleep(seconds)
            return True
            
        elif step_type == "coordinate_click":
            coords = step.get("coords", {})
            return self.click_by_coordinates(coords)
            
        elif step_type == "delay":
            delay = step.get("seconds", 1)
            self.log(f"Ожидание {delay} секунд")
            time.sleep(delay)
            return True
            
        else:
            self.log(f"Неизвестный тип шага: {step_type}", "ERROR")
            return False
    
    def run_automation(self) -> bool:
        """Запуск полной автоматизации"""
        self.log("🚀 Запуск автоматизации")
        
        try:
            steps = self.config.get("steps", [])
            step_delay = self.config["screen"]["step_delay"]
            
            for i, step in enumerate(steps):
                self.log(f"Шаг {i+1}/{len(steps)}")
                
                if not self.execute_step(step):
                    self.log(f"Шаг {i+1} не выполнен", "ERROR")
                    return False
                
                # Задержка между шагами (кроме последнего)
                if i < len(steps) - 1:
                    time.sleep(step_delay)
            
            self.log("🎉 Автоматизация завершена успешно!", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Критическая ошибка: {e}", "ERROR")
            return False
        finally:
            # Восстанавливаем FAILSAFE
            pyautogui.FAILSAFE = self.original_failsafe

# Пример использования
if __name__ == "__main__":
    # Кастомная конфигурация (опционально)
    custom_config = {
        "screen": {
            "step_delay": 3  # Увеличиваем задержку между шагами
        },
        "steps": [
            {
                "name": "find_browser",
                "type": "browser_detection", 
                "description": "Поиск и активация SunBrowser"
            },
            {
                "name": "click_google_signin",
                "type": "smart_google_click",
                "description": "Умный поиск и клик по кнопке Google"
            },
            {
                "name": "wait_for_google_page",
                "type": "wait_for_load",
                "seconds": 4,
                "description": "Ожидание загрузки страницы выбора аккаунта"
            },
            {
                "name": "click_email_account", 
                "type": "smart_email_click",
                "description": "Умный поиск и клик по аккаунту email"
            },
            {
                "name": "wait_for_permissions_page",
                "type": "wait_for_load",
                "seconds": 3,
                "description": "Ожидание загрузки страницы разрешений"
            },
            {
                "name": "click_continue_button",
                "type": "smart_continue_click", 
                "description": "Клик по кнопке Продолжить"
            }
        ]
    }
    
    # Создание и запуск автоматизации
    automation = BrowserAutomation(custom_config)
    automation.run_automation()