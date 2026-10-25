
import os
import time
import subprocess
import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0  # Отключаем встроенную задержку pyautogui

# Путь к картинке кнопки (положите скриншот элемента рядом со скриптом)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BTN_IMAGE = os.path.join(SCRIPT_DIR, "vscode_start_code_button.png")

def run_cmd(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return res.stdout.strip()

def get_vscode_window():
    """Ищет реальное видимое окно VS Code по классу или имени. Если не запущен — вернет None."""
    # Поиск по классу 'code' надежнее, так как заголовок меняется от имени файла
    win_ids = run_cmd(["xdotool", "search", "--onlyvisible", "--class", "code"]).split('\n')
    
    if not any(win_ids):
        win_ids = run_cmd(["xdotool", "search", "--onlyvisible", "--name", "Visual Studio Code"]).split('\n')

    for wid in reversed(win_ids):  # Берем последнее активное окно из списка
        if wid and "=" in run_cmd(["xprop", "-id", wid, "_NET_WM_DESKTOP"]):
            return wid
    return None

def click_by_image(image_path, retries=4, offset_y=0):
    """Быстро ищет кнопку на экране и кликает по ней."""
    if not os.path.exists(image_path):
        return False

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

        time.sleep(0.03)

    return False

def main():
    # 1. Проверяем, запущен ли VS Code (если нет — сразу выходим)
    vscode_win = get_vscode_window()
    if not vscode_win:
        return

    # 2. Запоминаем исходную позицию мыши и текущее активное окно
    orig_x, orig_y = pyautogui.position()
    active_win = run_cmd(["xdotool", "getactivewindow"])
    already_on_top = (active_win == vscode_win)

    try:
        # 3. Если VS Code под другими окнами — выводим его наверх
        if not already_on_top:
            subprocess.run(["xdotool", "windowactivate", "--sync", vscode_win], stderr=subprocess.DEVNULL)
            time.sleep(0.06)  # Короткая пауза на отрисовку окна

        # 4. Ищем элемент по картинке и кликаем
        click_by_image(BTN_IMAGE, retries=4, offset_y=0)

        # 5. Если доставали окно из-под других — возвращаем прежнее окно наверх
        if not already_on_top and active_win:
            time.sleep(0.03)
            subprocess.run(["xdotool", "windowactivate", "--sync", active_win], stderr=subprocess.DEVNULL)
    finally:
        # 6. В любом случае возвращаем мышь в исходную точку после всех переключений
        pyautogui.moveTo(orig_x, orig_y)

if __name__ == "__main__":
    main()