from flet import ElevatedButton, Text, colors, ControlState, ButtonStyle, padding, RoundedRectangleBorder
from flet import FontWeight, TextOverflow
def create_elevated_button(content, width, height, bgcolor, on_click, text_color=colors.BLACK, text_size=24):
    return ElevatedButton(
        content=Text(content, size=text_size, weight=FontWeight.BOLD, color=text_color, overflow=TextOverflow.ELLIPSIS),
        width=width,
        height=height,
        style=ButtonStyle(
            bgcolor={ControlState.DEFAULT: bgcolor, ControlState.PRESSED: bgcolor},
            shape=RoundedRectangleBorder(radius=8),
            padding=padding.symmetric(horizontal=16, vertical=8)
        ),
        on_click=on_click
    )

# def show_message(container, message, color):
#     if container.controls and isinstance(container.controls[0], Text):
#         container.controls.pop(0)
#     message_text = Text(message, color=color, size=16)
#     container.controls.insert(0, message_text)
#     container.update()
def get_text_size(screen_width):
    if screen_width > 600:
        return 24
    elif screen_width > 400:
        return 20
    else:
        return 16
