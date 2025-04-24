import tkinter as tk
import customtkinter as ctk
import sys

PADDING = 25
DEFAULT_FONT = "Arial" if sys.platform != "linux" else "DejaVu Sans"
PERSIAN_FONT = "Tahoma" if sys.platform == "win32" else DEFAULT_FONT
HOUSE_BASE_COLOR = "#AED6F1"

ROOM_COLOR_GUIDE = list({
    color: label for color, label in [
        ("#AED6F1", "پذیرایی / راهرو"),
        ("#FAD7A0", "آشپزخانه"),
        ("#D8BFD8", "اتاق خواب اصلی"),
        ("#FFDAB9", "اتاق خواب"),
        ("#E6E6FA", "حمام / سرویس"),
        ("#C8E6C9", "بالکن"),
        ("#D5DBDB", "انباری / کاربردی"),
    ]
}.items())

def draw_plan(canvas: tk.Canvas, plan_data: list, house_width_m: float, house_length_m: float, settings: dict):
    canvas.update_idletasks()
    canvas.delete("all")
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    wall_thickness_scale = settings.get('wall_thickness_scale', 0.01)

    if canvas_width <= 1 or canvas_height <= 1 or house_width_m <= 0 or house_length_m <= 0:
        return

    draw_area_w = canvas_width - 2 * PADDING
    draw_area_h = canvas_height - 2 * PADDING
    if draw_area_w <= 0 or draw_area_h <= 0:
        return

    scale = min(draw_area_w / house_width_m, draw_area_h / house_length_m)
    scaled_house_w = house_width_m * scale
    scaled_house_l = house_length_m * scale
    offset_x = PADDING + (draw_area_w - scaled_house_w) / 2
    offset_y = PADDING + (draw_area_h - scaled_house_l) / 2

    # رسم مستطیل زمینه (پذیرایی) که پشت همه قرار می‌گیرد
    canvas.create_rectangle(offset_x, offset_y, offset_x + scaled_house_w, offset_y + scaled_house_l,
                            fill="#AED6F1", outline="", width=0)
    
    # قاب کلی خانه (خط مشکی)
    canvas.create_rectangle(offset_x, offset_y, offset_x + scaled_house_w, offset_y + scaled_house_l,
                            outline="black", width=1)

    def draw_room(x, y, w, h, color):
        x0 = offset_x + x * scale
        y0 = offset_y + y * scale
        x1 = offset_x + (x + w) * scale
        y1 = offset_y + (y + h) * scale
        canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="black", width=1)
        return color

    used_colors = set()

    for room in plan_data:
        rect = room.get("rect")
        if rect and rect.is_valid():
            color = room.get("color", "#F0F0F0")
            draw_room(rect.x, rect.y, rect.w, rect.h, color)
            used_colors.add(color)

    # راهنمای رنگ
    legend_x = offset_x + scaled_house_w + 20
    legend_y = offset_y
    legend_spacing = 20
    for color, label in ROOM_COLOR_GUIDE:
        if color in used_colors:
            canvas.create_rectangle(legend_x, legend_y, legend_x + 20, legend_y + 15, fill=color, outline="black")
            canvas.create_text(legend_x + 30, legend_y + 7, anchor=tk.W, text=label, font=(PERSIAN_FONT, 9))
            legend_y += legend_spacing

    # نوار مقیاس
    possible_scales_m = [1, 2, 5, 10, 15, 20, 25, 50]
    scale_bar_length_m = 1
    for s in possible_scales_m:
        if house_width_m >= s * 1.5:
            scale_bar_length_m = s
        else:
            break

    scale_bar_length_px = scale_bar_length_m * scale
    bar_x = PADDING
    bar_y = canvas_height - PADDING / 1.5

    if bar_x + scale_bar_length_px < canvas_width - PADDING and scale_bar_length_px > 25:
        canvas.create_line(bar_x, bar_y, bar_x + scale_bar_length_px, bar_y, fill="black", width=2)
        canvas.create_line(bar_x, bar_y - 3, bar_x, bar_y + 3, fill="black", width=1)
        canvas.create_line(bar_x + scale_bar_length_px, bar_y - 3, bar_x + scale_bar_length_px, bar_y + 3, fill="black", width=1)
        text_x = min(bar_x + scale_bar_length_px / 2, canvas_width - PADDING)
        text_y = max(bar_y - 5, PADDING)
        canvas.create_text(text_x, text_y, text=f"{scale_bar_length_m} متر", fill="black", font=(PERSIAN_FONT, 9), anchor=tk.S)
