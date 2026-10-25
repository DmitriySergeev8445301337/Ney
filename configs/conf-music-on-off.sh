#!/bin/bash

# Координаты клика внутри окна Яндекс Музыки
CLICK_X=1480
CLICK_Y=1500

# Запоминаем ID текущего активного окна
CURRENT_WINDOW=$(xdotool getactivewindow)

# Ищем ID окна Яндекс Музыки
YM_WINDOW=$(xdotool search --name "Яндекс Музыка" | head -n 1)

if [ -z "$YM_WINDOW" ]; then
    YM_WINDOW=$(xdotool search --name "Yandex Music" | head -n 1)
fi

if [ -n "$YM_WINDOW" ]; then
    # Проверяем, активна ли Яндекс Музыка прямо сейчас
    if [ "$CURRENT_WINDOW" = "$YM_WINDOW" ]; then
        # Если мы уже в окне Музыки: просто кликаем без сворачивания/разворачивания
        xdotool mousemove --window "$YM_WINDOW" $CLICK_X $CLICK_Y click 1
    else
        # Если мы в другом окне: активируем Яндекс Музыку
        xdotool windowactivate --sync "$YM_WINDOW"
        
        # Кликаем по координатам
        xdotool mousemove --window "$YM_WINDOW" $CLICK_X $CLICK_Y click 1
        
        # Ждем ровно полсекунды (0.5)
        sleep 0.5
        
        # Возвращаем фокус на прежнее окно
        if [ -n "$CURRENT_WINDOW" ]; then
            xdotool windowactivate "$CURRENT_WINDOW"
        fi
    fi
else
    echo "Окно Яндекс Музыки не найдено!"
fi

