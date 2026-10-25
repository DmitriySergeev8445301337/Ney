#!/usr/bin/env bash
set -euo pipefail
APP_BIN="happ"
WIN_CLASS="happ"
SHOW_TIME=0.5
# Координаты кнопки ОТНОСИТЕЛЬНО ВЕРХНЕГО ЛЕВОГО УГЛА ОКНА happ (измените на свои)
CLICK_X=1500
CLICK_Y=400
# Задержка в секундах перед кликом (чтобы окно успело отобразиться)
CLICK_DELAY=0.1

if ! pgrep -x "$APP_BIN" >/dev/null; then
    "$APP_BIN" &
    for i in $(seq 1 20); do
        WIN_ID=$(xdotool search --class "$WIN_CLASS" 2>/dev/null | head -n1) || true
        [ -n "${WIN_ID:-}" ] && break
        sleep 0.1
    done
else
    WIN_ID=$(xdotool search --class "$WIN_CLASS" | head -n1)
fi

if [ -z "${WIN_ID:-}" ]; then
    echo "Окно приложения '$APP_BIN' не найдено" >&2
    exit 1
fi

# Отображаем окно поверх всех
xdotool windowactivate "$WIN_ID"
wmctrl -i -r "$WIN_ID" -b add,above

# Короткая пауза и клик по координатам внутри окна happ (1 = левая кнопка мыши)
sleep "$CLICK_DELAY"
xdotool mousemove --window "$WIN_ID" "$CLICK_X" "$CLICK_Y" click --window "$WIN_ID" 1

# Высчитываем оставшееся время показа окна (0.5 - 0.1 = 0.4 секунды)
REMAINING_TIME=$(echo "$SHOW_TIME - $CLICK_DELAY" | bc)
sleep "$REMAINING_TIME"

# Прячем окно обратно
wmctrl -i -r "$WIN_ID" -b remove,above
xdotool windowminimize "$WIN_ID"
