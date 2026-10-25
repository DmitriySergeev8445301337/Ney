import os
import time
import subprocess
import tkinter as tk
import pyautogui
import pytesseract
from PIL import ImageOps, ImageEnhance

# Отключаем защиту угла и встроенные задержки pyautogui
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# Настройки Happ
HAPP_LAUNCH_CMD = ["happ"]
HAPP_WINDOW_QUERY = "Happ"
DEFAULT_SERVER = "az3n54tkf6"  # ------------------------------------------------------------

# Координаты кнопки запуска (поменяй на свои)
BTN_CLICK_X = 1500
BTN_CLICK_Y = 400
# True — координаты считаются от левого верхнего угла самого окна Happ (не сбиваются при перемещении окна)
# False — абсолютные координаты экрана монитора
RELATIVE_TO_WINDOW = True

# Путь к картинке кнопки пинга и кэшу названий серверов в ОЗУ (/dev/shm)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PING_BTN_IMAGE = os.path.join(SCRIPT_DIR, "happ_ping_button.png")
CACHE_DIR = "/dev/shm/happ_server_cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def run_cmd(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return res.stdout.strip()


def get_happ_window():
    """Ищет реальное видимое окно Happ по имени или классу."""
    for flag in ("--name", "--class"):
        win_ids = run_cmd(["xdotool", "search", "--onlyvisible", flag, HAPP_WINDOW_QUERY]).split('\n')
        for wid in reversed(win_ids):
            if wid and "=" in run_cmd(["xprop", "-id", wid, "_NET_WM_DESKTOP"]):
                return wid
    return None


def get_window_region(win_id):
    """Быстро получает координаты и размер окна (X, Y, W, H)."""
    out = run_cmd(["xdotool", "getwindowgeometry", "--shell", win_id])
    geom = {}
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            geom[k] = int(v)
    if all(k in geom for k in ("X", "Y", "WIDTH", "HEIGHT")):
        return (geom["X"], geom["Y"], geom["WIDTH"], geom["HEIGHT"])
    return None


def launch_happ_if_needed():
    """Запускает Happ, если он закрыт, и ждет появления окна."""
    win_id = get_happ_window()
    if win_id:
        return win_id

    try:
        subprocess.Popen(HAPP_LAUNCH_CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        return None

    for _ in range(40):
        time.sleep(0.15)
        win_id = get_happ_window()
        if win_id:
            time.sleep(1.0)
            return win_id

    return None


def ask_server_name():
    """
    Открывает окно ввода сервера по центру экрана.
    Возвращает:
      - строку с названием сервера или командой пинга (Enter),
      - пустую строку "" (если стерли текст и нажали Enter -> просто нажать кнопку запуска),
      - None (Esc или "Отмена" -> ничего не делать).
    """
    result = {"name": None}

    root = tk.Tk()
    root.title("Happ — Выбор сервера")
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
        text="Какой сервер подключить в Happ?",
        fg="#FFFFFF",
        bg="#121212",
        font=("Sans", 16, "bold")
    )
    title_lbl.pack(anchor="w", pady=(0, 4))

    sub_lbl = tk.Label(
        container,
        text="Введите название и нажмите Enter (пустая строка — запуск, «пинг»/«ping» — замер пинга, Esc — отмена)",
        fg="#888888",
        bg="#121212",
        font=("Sans", 10)
    )
    sub_lbl.pack(anchor="w", pady=(0, 16))

    accent_color = "#00E5FF"

    entry_border = tk.Frame(container, bg=accent_color, padx=2, pady=2)
    entry_border.pack(fill="x", pady=(0, 18))

    entry = tk.Entry(
        entry_border,
        font=("Sans", 14),
        bg="#212121",
        fg="#FFFFFF",
        insertbackground=accent_color,
        selectbackground=accent_color,
        selectforeground="#000000",
        relief="flat",
        bd=6
    )
    entry.pack(fill="x")

    entry.insert(0, DEFAULT_SERVER)
    entry.select_range(0, tk.END)
    entry.icursor(tk.END)
    entry.focus_force()

    def on_submit(event=None):
        result["name"] = entry.get().strip()
        root.withdraw()
        root.update()
        root.destroy()

    def on_cancel(event=None):
        result["name"] = None
        root.withdraw()
        root.update()
        root.destroy()

    btn_frame = tk.Frame(container, bg="#121212")
    btn_frame.pack(fill="x")

    submit_btn = tk.Button(
        btn_frame,
        text="Подключить ↵",
        command=on_submit,
        bg=accent_color,
        fg="#121212",
        activebackground="#00B8D4",
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


def detect_ocr_lang(text):
    """Подгружает только нужную языковую модель Tesseract для максимальной скорости."""
    has_cyr = any('а' <= ch <= 'я' or ch == 'ё' for ch in text.lower())
    has_lat = any('a' <= ch <= 'z' for ch in text.lower())
    if has_cyr and not has_lat:
        return 'rus'
    if has_lat and not has_cyr:
        return 'eng'
    return 'rus+eng'


def find_and_click_text(target_text, region=None, retries=3):
    """
    Сначала ищет название сервера по кэшированному слепку в ОЗУ (за ~0.03 сек).
    Если слепка еще нет — находит через быстрый OCR внутри окна и кэширует.
    """
    target_lower = target_text.lower()
    safe_name = "".join(c if c.isalnum() else "_" for c in target_lower)
    cache_img_path = os.path.join(CACHE_DIR, f"srv_{safe_name}.png")

    # 1. Мгновенный поиск по кэшу в RAM
    if os.path.exists(cache_img_path):
        try:
            loc = pyautogui.locateCenterOnScreen(cache_img_path, region=region, confidence=0.85, grayscale=True)
            if loc:
                pyautogui.click(loc.x, loc.y)
                return True
        except Exception:
            pass

    # 2. Быстрый OCR только по области окна Happ
    target_words = target_lower.split()
    lang = detect_ocr_lang(target_lower)
    offset_x = region[0] if region else 0
    offset_y = region[1] if region else 0

    for _ in range(retries):
        screenshot = pyautogui.screenshot(region=region)
        gray = ImageOps.grayscale(screenshot)
        processed_img = ImageEnhance.Contrast(gray).enhance(2.0)

        data = pytesseract.image_to_data(
            processed_img,
            output_type=pytesseract.Output.DICT,
            lang=lang,
            config='--psm 11 --oem 1'
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
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]

                try:
                    pad = 4
                    crop_box = (
                        max(0, x - pad),
                        max(0, y - pad),
                        min(screenshot.width, x + w + pad),
                        min(screenshot.height, y + h + pad)
                    )
                    screenshot.crop(crop_box).save(cache_img_path)
                except Exception:
                    pass

                click_x = offset_x + x + (w // 2)
                click_y = offset_y + y + (h // 2)
                pyautogui.click(click_x, click_y)
                return True

        time.sleep(0.02)

    return False


def click_button_by_image(image_path, region=None, retries=5):
    """Быстро ищет кнопку (например, измерения пинга) по картинке и кликает по ней."""
    if not os.path.exists(image_path):
        return False

    for _ in range(retries):
        try:
            location = pyautogui.locateCenterOnScreen(
                image_path,
                region=region,
                confidence=0.85,
                grayscale=False
            )
        except TypeError:
            location = pyautogui.locateCenterOnScreen(image_path, region=region)
        except pyautogui.ImageNotFoundException:
            location = None

        if location:
            pyautogui.click(location.x, location.y)
            return True

        time.sleep(0.03)

    return False


def click_connect_button(win_id):
    """Мгновенно кликает по заданным координатам кнопки."""
    if RELATIVE_TO_WINDOW and win_id:
        subprocess.run(
            ["xdotool", "mousemove", "--window", win_id, str(BTN_CLICK_X), str(BTN_CLICK_Y), "click", "1"],
            stderr=subprocess.DEVNULL
        )
    else:
        pyautogui.click(BTN_CLICK_X, BTN_CLICK_Y)


def main():
    prev_active_win = run_cmd(["xdotool", "getactivewindow"])
    orig_x, orig_y = pyautogui.position()

    # Спрашиваем название сервера
    server_name = ask_server_name()
    if server_name is None:
        return

    # Проверяем, был ли запущен Happ до старта
    happ_win = get_happ_window()
    was_running = happ_win is not None

    if not was_running:
        happ_win = launch_happ_if_needed()
        if not happ_win:
            return
        already_on_top = False
    else:
        already_on_top = (prev_active_win == happ_win)

    try:
        # Если Happ не на самом верху — выводим его наверх
        if not already_on_top:
            subprocess.run(["xdotool", "windowactivate", "--sync", happ_win], stderr=subprocess.DEVNULL)
            time.sleep(0.06)

        # ЕСЛИ ВВЕЛИ "пинг" ИЛИ "ping" (в любом регистре):
        # жмем кнопку пинга по картинке и выходим, НЕ пряча окно обратно
        if server_name.lower() in ("пинг", "ping"):
            region = get_window_region(happ_win)
            click_button_by_image(PING_BTN_IMAGE, region=region, retries=5)
            return

        # 1. Если введено название сервера — 1 клик по надписи сервера
        if server_name != "":
            region = get_window_region(happ_win)
            find_and_click_text(server_name, region=region, retries=2)
            time.sleep(0.04)

        # 2. 1 клик по координатам кнопки запуска
        click_connect_button(happ_win)

        # Если Happ уже был запущен, но находился под другими окнами — прячем его обратно
        if was_running and not already_on_top and prev_active_win:
            time.sleep(0.04)
            subprocess.run(["xdotool", "windowactivate", "--sync", prev_active_win], stderr=subprocess.DEVNULL)
    finally:
        # Всегда возвращаем мышь на исходную координату
        pyautogui.moveTo(orig_x, orig_y)


if __name__ == "__main__":
    main()