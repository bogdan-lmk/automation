import tkinter as tk
import time
import threading

def get_mouse_pos():
    """Получает позицию мыши без дополнительных библиотек"""
    try:
        # Пытаемся получить позицию через tkinter
        x = root.winfo_pointerx()
        y = root.winfo_pointery()
        return x, y
    except:
        return 0, 0

def update_position():
    """Обновляет отображение координат"""
    x, y = get_mouse_pos()
    x_label.config(text=f"X: {x}")
    y_label.config(text=f"Y: {y}")
    root.after(50, update_position)  # Обновление каждые 50мс

# Создаем окно
root = tk.Tk()
root.title("Координаты мыши")
root.geometry("200x100")
root.attributes('-topmost', True)  # Поверх других окон

# Создаем метки для координат
x_label = tk.Label(root, text="X: 0", font=("Arial", 14))
x_label.pack(pady=10)

y_label = tk.Label(root, text="Y: 0", font=("Arial", 14))
y_label.pack(pady=5)

# Запускаем обновление
update_position()

# Запускаем приложение
root.mainloop()