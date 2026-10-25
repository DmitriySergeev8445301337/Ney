import os
import time
import subprocess
import tkinter as tk
import pyautogui
import pytesseract
from PIL import ImageOps, ImageEnhance

# Отключаем защиту угла экрана pyautogui, чтобы спокойно уводить мышь в (5, 5)
pyautogui.FAILSAFE = False

# Команда запуска Яндекс Музыки
YM_LAUNCH_CMD = ["yandexmusic"]

# Путь к картинке кнопки "Слушать"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LISTEN_BTN_IMAGE = os.path.join(SCRIPT_DIR, "listen_btn.png")

def run_cmd(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return res.stdout.strip()

def get_ym_window():
    """Ищет реальное видимое окно Яндекс Музыки."""
    win_ids = run_cmd(["xdotool", "search", "--name", "Яндекс Музыка"]).split('\n')
    for wid in win_ids:
        if wid and "=" in run_cmd(["xprop", "-id", wid, "_NET_WM_DESKTOP"]):
            return wid
    return None

def ensure_yandex_music_running():
    """Активирует окно Яндекс Музыки или запускает программу, если она закрыта."""
    win_id = get_ym_window()
    
    if not win_id:
        try:
            subprocess.Popen(YM_LAUNCH_CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            return False

        for _ in range(40):
            time.sleep(0.25)
            win_id = get_ym_window()
            if win_id:
                time.sleep(2.5)
                break

    if not win_id:
        return False

    subprocess.run(["xdotool", "windowactivate", "--sync", win_id], stderr=subprocess.DEVNULL)
    time.sleep(0.05)
    return True

def ask_playlist_name():
    """
    Открывает окно ввода по центру экрана.
    Возвращает:
      - строку с названием (если ввели текст и нажали Enter),
      - пустую строку "" (если стерли текст и нажали Enter — режим «просто запуск»),
      - None (если нажали Esc, кнопку «Отмена» или закрыли окно).
    """
    result = {"name": None}

    root = tk.Tk()
    root.title("Яндекс Музыка — Выбор плейлиста")
    root.attributes("-topmost", True)
    root.configure(bg="#121212")
    root.resizable(False, False)

    w, h = 1020, 240
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    container = tk.Frame(root, bg="#121212", padx=35, pady=25)
    container.pack(fill="both", expand=True)

    title_lbl = tk.Label(
        container,
        text="Какой плейлист включить?",
        fg="#FFFFFF",
        bg="#121212",
        font=("Sans", 16, "bold")
    )
    title_lbl.pack(anchor="w", pady=(0, 4))

    sub_lbl = tk.Label(
        container,
        text="Введите название и нажмите Enter",
        fg="#888888",
        bg="#121212",
        font=("Sans", 10)
    )
    sub_lbl.pack(anchor="w", pady=(0, 16))

    entry_border = tk.Frame(container, bg="#FED42B", padx=2, pady=2)
    entry_border.pack(fill="x", pady=(0, 18))

    entry = tk.Entry(
        entry_border,
        font=("Sans", 14),
        bg="#212121",
        fg="#FFFFFF",
        insertbackground="#FED42B",
        selectbackground="#FED42B",
        selectforeground="#000000",
        relief="flat",
        bd=6
    )
    entry.pack(fill="x")

    default_text = "пупупу"
    entry.insert(0, default_text)
    entry.select_range(0, tk.END)
    entry.icursor(tk.END)
    entry.focus_force()

    def on_submit(event=None):
        # Сохраняем строку (даже если она пустая "")
        result["name"] = entry.get().strip()
        root.withdraw()
        root.update()
        root.destroy()

    def on_cancel(event=None):
        # При отмене оставляем None
        result["name"] = None
        root.withdraw()
        root.update()
        root.destroy()

    btn_frame = tk.Frame(container, bg="#121212")
    btn_frame.pack(fill="x")

    submit_btn = tk.Button(
        btn_frame,
        text="Слушать ↵",
        command=on_submit,
        bg="#FED42B",
        fg="#121212",
        activebackground="#E5BE26",
        activeforeground="#121212", 
        font=("Sans", 11, "bold"),
        relief="flat",
        padx=20,
        pady=6,
        cursor="hand2",
        bd=0
    )
    submit_btn.pack(side="right")

    cancel_btn = tk.Button(
        btn_frame,
        text="Отмена",
        command=on_cancel,
        bg="#242424",
        fg="#CCCCCC",
        activebackground="#333333",
        activeforeground="#FFFFFF",
        font=("Sans", 11),
        relief="flat",
        padx=16,
        pady=6,
        cursor="hand2",
        bd=0
    )
    cancel_btn.pack(side="right", padx=(0, 10))

    entry.bind("<Return>", on_submit)
    root.bind("<Escape>", on_cancel)
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    root.mainloop()
    return result["name"]

def preprocess_for_ocr(pil_img, scale=2):
    """Увеличивает скриншот и повышает контраст, чтобы Tesseract не пропускал слова."""
    w, h = pil_img.size
    enlarged = pil_img.resize((w * scale, h * scale))
    gray = ImageOps.grayscale(enlarged)
    contrasted = ImageEnhance.Contrast(gray).enhance(2.0)
    return contrasted

def find_and_click_text(target_text, retries=4, double_click=False):
    """Ищет название плейлиста с предобработкой изображения и несколькими попытками."""
    target_lower = target_text.lower()
    target_words = target_lower.split()
    scale = 2

    for attempt in range(retries):
        time.sleep(0.05)

        screenshot = pyautogui.screenshot()
        processed_img = preprocess_for_ocr(screenshot, scale=scale)

        data = pytesseract.image_to_data(
            processed_img,
            output_type=pytesseract.Output.DICT,
            lang='rus+eng',
            config='--psm 11'
        )

        n_boxes = len(data['text'])
        for i in range(n_boxes):
            word = data['text'][i].strip().lower()
            if not word:
                continue

            matched = False
            if target_lower in word:
                matched = True
            elif len(target_words) > 1 and target_words[0] in word:
                phrase = " ".join(data['text'][i:i+len(target_words)]).strip().lower()
                if target_lower in phrase:
                    matched = True

            if matched:
                x = data['left'][i] // scale
                y = data['top'][i] // scale
                w = data['width'][i] // scale
                h = data['height'][i] // scale

                click_x = x + (w // 2)
                click_y = y + (h // 2)

                if double_click:
                    pyautogui.doubleClick(click_x, click_y)
                else:
                    pyautogui.click(click_x, click_y)
                return True

        time.sleep(0.1)

    return False

def click_button_by_image(image_path, retries=8, offset_y=0):
    """Ищет кнопку на экране по цветному шаблону и кликает в её центр (с возможностью смещения по Y)."""
    if not os.path.exists(image_path):
        return False

    pyautogui.moveTo(5, 5)

    for _ in range(retries):
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=0.85, grayscale=False)
        except TypeError:
            location = pyautogui.locateCenterOnScreen(image_path)
        except pyautogui.ImageNotFoundException:
            location = None

        if location:
            pyautogui.click(location.x, location.y + offset_y)
            return True

        time.sleep(0.1)

    return False

def main():
    playlist_name = ask_playlist_name()
    
    # Если нажали Esc или "Отмена" — ничего не делаем
    if playlist_name is None:
        return

    # Запускаем или разворачиваем Яндекс Музыку
    if not ensure_yandex_music_running():
        return

    # Если строка была пустой (например, нажали Backspace -> Enter), 
    # то после запуска/активации окна просто выходим
    if playlist_name == "":
        return

    if not find_and_click_text(playlist_name, retries=4, double_click=False):
        return

    # Даем странице плейлиста время на открытие и ищем кнопку
    time.sleep(0.1)
    click_button_by_image(LISTEN_BTN_IMAGE, retries=8, offset_y=0)

if __name__ == "__main__":
    main()