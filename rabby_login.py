import pyautogui
import time

print("Ожидаю появление поля Rabby Wallet...")

# Пытаемся найти изображение поля — до 40 секунд
for i in range(40):
    try:
        # Поиск поля по скриншоту
        location = pyautogui.locateCenterOnScreen('src/adspower_automation/strategies/rabby_password_field.png', confidence=0.8)
        if location:
            print(f"Поле найдено на координатах {location}")
            pyautogui.click(location)
            time.sleep(0.3)
            pyautogui.write('rabbywallet', interval=0.1)
            pyautogui.press('enter')
            print("Пароль введён и отправлен.")
            break
    except Exception as e:
        # Можно добавить логирование ошибок для отладки
        # print(f"Попытка {i+1}: {e}")
        pass
    time.sleep(1)
else:
    print("❌ Поле пароля не найдено за 40 секунд.")
    exit()

# Ожидаем появления кнопки Sign
print("Ожидаю появление кнопки Sign...")
time.sleep(2)  # Даём время на загрузку следующего экрана

# Два клика по точным координатам кнопки SIGN с интервалом 1 секунда
print("Первый клик по кнопке Sign на координатах (1143, 775)")
pyautogui.click(1143, 775)
time.sleep(1)
print("Второй клик по кнопке Sign")
pyautogui.click(1143, 775)
print("✅ Кнопка Sign нажата два раза!")

print("Скрипт завершён.")