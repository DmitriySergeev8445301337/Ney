
#!/bin/bash

# Координаты клика внутри окна VS Code (подставь свои)
CLICK_X=2900
CLICK_Y=100

# Ищем видимое окно VS Code по классу (надежнее, чем по имени, так как в заголовке меняется имя файла)
VSCODE_WINDOW=$(xdotool search --onlyvisible --class "code" | tail -n 1)

# Если по классу не нашлось, ищем по тексту в заголовке окна
if [ -z "$VSCODE_WINDOW" ]; then
    VSCODE_WINDOW=$(xdotool search --onlyvisible --name "Visual Studio Code" | head -n 1)
fi

if [ -n "$VSCODE_WINDOW" ]; then
    # Выводим VS Code на передний план (делаем главным окном) и ждем фокуса
    xdotool windowactivate --sync "$VSCODE_WINDOW" 2>/dev/null

    # Небольшая пауза, чтобы окно успело отрисоваться поверх остальных
    sleep 0.1

    # Перемещаем курсор относительно окна VS Code и кликаем левой кнопкой мыши
    xdotool mousemove --window "$VSCODE_WINDOW" "$CLICK_X" "$CLICK_Y" click 1
else
    echo "Окно VS Code не найдено (редактор не запущен)!"
fi

