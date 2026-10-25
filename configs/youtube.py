# import subprocess
# import time

# BROWSERS = ("chromium", "chrome", "firefox", "brave", "vivaldi", "opera", "yandex-browser")

# def run_cmd(cmd):
#     res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
#     return res.stdout.strip()

# def toggle_music():
#     # 1. Пробуем переключить в фоне через playerctl (ищем плеер, который НЕ является браузером)
#     players = run_cmd(["playerctl", "--list-all"]).split('\n')
#     for player in players:
#         player_low = player.lower()
#         if not player_low:
#             continue
            
#         # Если это не браузер, проверяем имя процесса или метаданные на принадлежность к Музыке
#         if not any(b in player_low for b in BROWSERS):
#             meta = run_cmd(["playerctl", "--player", player, "metadata"]).lower()
#             if "yandex" in player_low or "music" in player_low or "яндекс" in meta or "yandex" in meta:
#                 subprocess.run(["playerctl", "--player", player, "play-pause"])
#                 print(f"Яндекс Музыка переключена в фоне ({player})")
#                 return

#     # 2. Если клиент не виден в playerctl — переключаем через окно программы
#     win_ids = run_cmd(["xdotool", "search", "--name", "Яндекс Музыка"]).split('\n')
    
#     # Оставляем только реальное видимое окно (защита от ошибки _NET_WM_DESKTOP)
#     real_wins = [w for w in win_ids if w and "=" in run_cmd(["xprop", "-id", w, "_NET_WM_DESKTOP"])]

#     if real_wins:
#         target_win = real_wins[0]
#         active_win = run_cmd(["xdotool", "getactivewindow"])

#         subprocess.run(["xdotool", "windowactivate", target_win], stderr=subprocess.DEVNULL)
#         time.sleep(0.03)
#         subprocess.run(["xdotool", "key", "space"], stderr=subprocess.DEVNULL)
#         time.sleep(0.03)

#         # Возвращаем фокус в окно, где ты работал
#         if active_win and active_win != target_win:
#             subprocess.run(["xdotool", "windowactivate", active_win], stderr=subprocess.DEVNULL)
            
#         print("Яндекс Музыка переключена через окно программы.")
#         return

#     print("Программа Яндекс Музыка не найдена.")

# if __name__ == "__main__":
#     toggle_music()


print("+++++++-----")