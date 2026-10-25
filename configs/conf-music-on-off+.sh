#!/bin/bash

BUTTON_IMG="music_play_button.png"
TMP_SCREEN="/dev/shm/ym_window.png"

click_by_image() {
    # Делаем скриншот окна без альфа-канала (чтобы цвета 100% совпадали с шаблоном)
    import -window "$YM_WINDOW" -alpha off "$TMP_SCREEN"
    
    # Ищем кнопку (-t 5000 дает допуск на легкое сглаживание шрифтов/иконок)
    COORDS=$(visgrep -t 5000 "$TMP_SCREEN" "$BUTTON_IMG" | head -n 1 | awk '{print $1}')
    rm -f "$TMP_SCREEN"

    if [ -n "$COORDS" ]; then
        CLICK_X=${COORDS%,*}
        CLICK_Y=${COORDS#*,}
        # Кликаем со смещением +5 пикселей от левого верхнего угла вырезанного кусочка
        xdotool mousemove --window "$YM_WINDOW" $((CLICK_X + 5)) $((CLICK_Y + 5)) click 1
    else
        echo "Кнопка не найдена на скриншоте окна!"
        notify-send "Яндекс Музыка" "Кнопка не найдена (пересоздайте ~/button.png)"
    fi
}

# Запоминаем ID текущего активного окна
CURRENT_WINDOW=$(xdotool getactivewindow)

# Ищем ID окна Яндекс Музыки
YM_WINDOW=$(xdotool search --name "Яндекс Музыка" | head -n 1)

if [ -z "$YM_WINDOW" ]; then
    YM_WINDOW=$(xdotool search --name "Yandex Music" | head -n 1)
fi

if [ -n "$YM_WINDOW" ]; then
    if [ "$CURRENT_WINDOW" = "$YM_WINDOW" ]; then
        click_by_image
    else
        xdotool windowactivate --sync "$YM_WINDOW"
        
        # Даем 0.15 сек на фактическую отрисовку окна видеокартой после активации
        sleep 0.15
        
        click_by_image
        
        sleep 0.5
        
        if [ -n "$CURRENT_WINDOW" ]; then
            xdotool windowactivate "$CURRENT_WINDOW"
        fi
    fi
else
    echo "Окно Яндекс Музыки не найдено!"
fi