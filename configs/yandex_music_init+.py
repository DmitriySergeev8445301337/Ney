import os
import time
import subprocess
import tkinter as tk
import pyautogui
import pytesseract
from PIL import ImageOps, ImageEnhance

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

YM_LAUNCH_CMD = ["yandexmusic"]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LISTEN_BTN_IMAGE = os.path.join(SCRIPT_DIR, "listen_btn.png")
CACHE_DIR = "/dev/shm/ym_playlist_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def run_cmd(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return res.stdout.strip()

def get_ym_window():
    """Ищет реальное видимое окно Яндекс Музыки."""
    win_ids = run_cmd(["xdotool", "search", "--onlyvisible", "--name", "Яндекс Музыка"]).split('\n')
    for wid in win_ids:
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

def ensure_yandex_music_running():
    """Активирует окно Яндекс Музыки и возвращает его ID."""
    win_id = get_ym_window()
    
    if not win_id:
        try:
            subprocess.Popen(YM_LAUNCH_CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            return None

        for _ in range(40):
            time.sleep(0.2)
            win_id = get_ym_window()
            if win_id:
                time.sleep(2.0)
                break

    if not win_id:
        return None

    subprocess.run(["xdotool", "windowactivate", "--sync", win_id], stderr=subprocess.DEVNULL)
    return win_id

def ask_playlist_name():
    """Открывает окно ввода по центру экрана."""
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

def detect_ocr_lang(text):
    has_cyr = any('а' <= ch <= 'я' or ch == 'ё' for ch in text.lower())
    has_lat = any('a' <= ch <= 'z' for ch in text.lower())
    if has_cyr and not has_lat:
        return 'rus'
    if has_lat and not has_cyr:
        return 'eng'
    return 'rus+eng'

def find_and_click_text(target_text, region=None, retries=3, double_click=False):
    target_lower = target_text.lower()
    safe_name = "".join(c if c.isalnum() else "_" for c in target_lower)
    cache_img_path = os.path.join(CACHE_DIR, f"pl_{safe_name}.png")

    if os.path.exists(cache_img_path):
        try:
            loc = pyautogui.locateCenterOnScreen(cache_img_path, region=region, confidence=0.88)
            if loc:
                if double_click:
                    pyautogui.doubleClick(loc.x, loc.y)
                else:
                    pyautogui.click(loc.x, loc.y)
                return True
        except Exception:
            pass

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

                if double_click:
                    pyautogui.doubleClick(click_x, click_y)
                else:
                    pyautogui.click(click_x, click_y)
                return True

        time.sleep(0.02)

    return False

def is_yandex_yellow(rgb):
    """Проверяет, что пиксель имеет фирменный желтый цвет кнопки Яндекс Музыки (#FED42B)."""
    r, g, b = rgb[:3]
    return r > 200 and g > 170 and b < 110 and (r - b) > 110

def locate_yellow_button(image_path, search_region):
    """Находит кнопку по шаблону и отсеивает ложные срабатывания на обложке по цвету."""
    try:
        matches = list(pyautogui.locateAllOnScreen(
            image_path,
            region=search_region,
            confidence=0.88,
            grayscale=False
        ))
    except TypeError:
        matches = list(pyautogui.locateAllOnScreen(image_path, region=search_region))
    except pyautogui.ImageNotFoundException:
        matches = []

    if not matches:
        return None

    # Сортируем снизу вверх (кнопка всегда ниже обложки)
    matches.sort(key=lambda b: b.top, reverse=True)

    for box in matches:
        cx, cy = pyautogui.center(box)
        # Проверяем пиксели вокруг центра (на случай если в самом центре черная буква "С" или треугольник)
        for dx, dy in ((0, 0), (-15, 0), (15, 0), (0, -8), (0, 8)):
            try:
                if is_yandex_yellow(pyautogui.pixel(int(cx + dx), int(cy + dy))):
                    return (int(cx), int(cy))
            except Exception:
                continue

    # Если проверка пикселя не сработала, берем самый нижний результат
    best = matches[0]
    c = pyautogui.center(best)
    return (int(c.x), int(c.y))

def click_button_by_image(image_path, region=None, retries=12):
    """
    Ждет появления кнопки 'Слушать' и убеждается, что страница перестала съезжать вниз
    из-за подгрузки обложки, прежде чем кликнуть.
    """
    if not os.path.exists(image_path):
        return False

    # Уводим курсор с пути, чтобы всплывающая подсказка от прошлой карточки не закрыла кнопку
    pyautogui.moveTo(50, 50)

    search_region = region
    if region and region[3] > 350:
        # Отрезаем верхние 180 пикселей (шапка) и нижние 90 пикселей (нижний плеер)
        top_cut = 180
        bottom_cut = 90
        search_region = (
            region[0],
            region[1] + top_cut,
            region[2],
            max(100, region[3] - top_cut - bottom_cut)
        )

    last_pos = None

    for _ in range(retries):
        pos = locate_yellow_button(image_path, search_region)

        if pos:
            # Если мы нашли кнопку, проверяем через 40 мс — не съехала ли она ниже из-за загрузки обложки
            if last_pos and abs(pos[1] - last_pos[1]) <= 5:
                pyautogui.click(pos[0], pos[1])
                return True
            
            last_pos = pos
            time.sleep(0.045)
        else:
            time.sleep(0.03)

    # Если цикл закончился, но кнопку мы видели в последнем кадре — кликаем по ней
    if last_pos:
        pyautogui.click(last_pos[0], last_pos[1])
        return True

    return False

def main():
    playlist_name = ask_playlist_name()
    
    if playlist_name is None:
        return

    orig_x, orig_y = pyautogui.position()

    win_id = ensure_yandex_music_running()
    if not win_id:
        return

    if playlist_name == "":
        return

    try:
        region = get_window_region(win_id)

        if not find_and_click_text(playlist_name, region=region, retries=3, double_click=False):
            return

        # Короткая пауза на начало переключения страницы и поиск со стабилизацией
        time.sleep(0.06)
        click_button_by_image(LISTEN_BTN_IMAGE, region=region, retries=12)
    finally:
        # Возвращаем мышь туда, где она была до запуска
        pyautogui.moveTo(orig_x, orig_y)

if __name__ == "__main__":
    main()