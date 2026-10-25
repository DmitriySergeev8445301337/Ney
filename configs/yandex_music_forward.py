



import os
import time
import subprocess
import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0  # Отключаем встроенную задержку pyautogui (0.1 сек после каждого действия)

# Имя картинки кнопки в папке со скриптом (можешь поменять на свое)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BTN_IMAGE = os.path.join(SCRIPT_DIR, "music_forward_button.png")

def run_cmd(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return res.stdout.strip()

def get_ym_window():
    """Ищет реальное окно Яндекс Музыки. Если не запущена — вернет None."""
    win_ids = run_cmd(["xdotool", "search", "--name", "Яндекс Музыка"]).split('\n')
    for wid in win_ids:
        if wid and "=" in run_cmd(["xprop", "-id", wid, "_NET_WM_DESKTOP"]):
            return wid
    return None

def click_by_image(image_path, retries=5, offset_y=0):
    """Быстро ищет кнопку по картинке и кликает по ней, возвращая курсор на место."""
    if not os.path.exists(image_path):
        return False

    # Запоминаем, где была мышь, и уводим в угол, чтобы не подсвечивать элементы
    orig_x, orig_y = pyautogui.position()
    # pyautogui.moveTo(5, 5)

    for _ in range(retries):
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=0.85, grayscale=False)
        except TypeError:
            location = pyautogui.locateCenterOnScreen(image_path)
        except pyautogui.ImageNotFoundException:
            location = None

        if location:
            pyautogui.click(location.x, location.y + offset_y)
            pyautogui.moveTo(orig_x, orig_y)  # Возвращаем мышь туда, где она была
            return True

        time.sleep(0.01)

    pyautogui.moveTo(orig_x, orig_y)
    return False

def main():
    # 1. Проверяем, запущена ли Яндекс Музыка (если нет — сразу выходим)
    ym_win = get_ym_window()
    if not ym_win:
        return

    # 2. Проверяем, какое окно сейчас активно (на самом верху)
    active_win = run_cmd(["xdotool", "getactivewindow"])
    already_on_top = (active_win == ym_win)

    # 3. Если Яндекс Музыка под другими окнами — выводим ее наверх
    if not already_on_top:
        subprocess.run(["xdotool", "windowactivate", "--sync", ym_win], stderr=subprocess.DEVNULL)
        time.sleep(0.01)  # Минимальная пауза на отрисовку окна

    # 4. Нажимаем на кнопку по картинке
    click_by_image(BTN_IMAGE, retries=5, offset_y=0)

    # 5. Если мы доставали окно из-под других — прячем его обратно
    if not already_on_top and active_win:
        time.sleep(0.1)
        subprocess.run(["xdotool", "windowactivate", active_win], stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    main()