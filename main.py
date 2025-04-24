import sys
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from plan_generator import (generate_plans,
                            DEFAULT_MIN_ROOM_DIM, DEFAULT_MIN_BATH_DIM,
                            DEFAULT_MIN_STOR_BALC_DIM, DEFAULT_ASPECT_RATIO_LIMIT,
                            DEFAULT_WALL_THICKNESS_SCALE, DEFAULT_LABEL_FONT_SIZE_SCALE, # Import new defaults
                            PERSIAN_NAMES)
from plan_drawer import draw_plan
import traceback

# Set default theme and appearance mode early
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class WelcomeScreen(ctk.CTkToplevel):
    """ Initial welcome screen """
    def __init__(self, parent):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.parent = parent
        self.title("") # No title bar text
        self.protocol("WM_DELETE_WINDOW", self.close_app) # Close main app if welcome screen closed

        persian_font = "Tahoma" if sys.platform == "win32" else "Arial"

        # Fullscreen setup
        self.attributes('-fullscreen', True)
        self.bind("<Escape>", self.exit_fullscreen_and_start)

        # Frame to center content
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        welcome_text = """
به مولد نقشه خانه خوش آمدید!

این برنامه به شما کمک می‌کند تا طرح‌های اولیه و شماتیک
برای نقشه خانه خود بر اساس ابعاد وارد شده ایجاد کنید.

این برنامه توسط امیرکیا علیقلی زاد و شایان فلاح نژاد ساخته شده است.

برای شروع، روی دکمه زیر کلیک کنید یا کلید Enter را فشار دهید.
برای خروج از حالت تمام صفحه، کلید Esc را فشار دهید.
"""
        self.label = ctk.CTkLabel(center_frame, text=welcome_text, justify="center", font=(persian_font, 16), wraplength=600)
        self.label.pack(pady=30, padx=20)

        self.start_button = ctk.CTkButton(center_frame, text="ورود به برنامه", command=self.start_main_app, font=(persian_font, 14))
        self.start_button.pack(pady=20)
        self.start_button.focus_set()
        self.bind("<Return>", lambda event: self.start_main_app())

        self.exit_button = ctk.CTkButton(self, text="X", width=30, height=30, command=self.exit_fullscreen_and_start,
                                         fg_color="transparent", text_color="gray", hover=False)
        self.exit_button.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne")


    def exit_fullscreen_and_start(self, event=None):
        self.attributes('-fullscreen', False)
        self.start_main_app()

    def start_main_app(self):
        self.destroy()
        self.parent.deiconify()
        self.parent.focus_force()
        self.parent.entry_width.focus_set()

    def close_app(self):
        self.destroy()
        self.parent.quit()


class SettingsDialog(ctk.CTkToplevel):
    """ Toplevel window for settings - Docked and Scrollable """
    def __init__(self, parent, current_settings):
        super().__init__(parent)
        # Remove grab_set and transient for non-modal behavior
        # self.transient(parent)
        # self.grab_set()
        self.title("تنظیمات")
        self.parent = parent
        self.settings = current_settings.copy()
        self.protocol("WM_DELETE_WINDOW", self.close_dialog) # Handle closing via 'X'

        # --- Positioning (Dock Right) ---
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        win_w = 380 # Fixed width for the settings panel
        win_h = parent_h # Match parent height
        # Position to the right of the parent window
        win_x = parent_x + parent_w
        win_y = parent_y

        # Clamp position to screen boundaries (basic check)
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        if win_x + win_w > screen_w:
            win_x = screen_w - win_w
        if win_y + win_h > screen_h:
            win_y = screen_h - win_h
        win_x = max(0, win_x)
        win_y = max(0, win_y)

        self.geometry(f"{win_w}x{win_h}+{win_x}+{win_y}")
        self.resizable(False, True) # Allow vertical resize

        persian_font = "Tahoma" if sys.platform == "win32" else "Arial"

        # --- Scrollable Frame ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="تنظیمات برنامه", label_font=(persian_font, 14))
        self.scroll_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Dimension Settings ---
        dim_label = ctk.CTkLabel(self.scroll_frame, text="تنظیمات ابعاد", font=(persian_font, 13, 'bold'), anchor='e')
        dim_label.pack(pady=(5, 10), anchor='e', padx=10)

        self.label_min_room = ctk.CTkLabel(self.scroll_frame, text=":حداقل ابعاد اتاق اصلی (متر)", font=(persian_font, 12))
        self.label_min_room.pack(pady=(0, 2), anchor='e', padx=10)
        self.entry_min_room = ctk.CTkEntry(self.scroll_frame, justify='right')
        self.entry_min_room.insert(0, str(self.settings.get('min_room_dim', DEFAULT_MIN_ROOM_DIM)))
        self.entry_min_room.pack(pady=(0, 10), fill='x', padx=10)

        self.label_min_bath = ctk.CTkLabel(self.scroll_frame, text=":حداقل ابعاد سرویس/حمام (متر)", font=(persian_font, 12))
        self.label_min_bath.pack(pady=(5, 2), anchor='e', padx=10)
        self.entry_min_bath = ctk.CTkEntry(self.scroll_frame, justify='right')
        self.entry_min_bath.insert(0, str(self.settings.get('min_bath_dim', DEFAULT_MIN_BATH_DIM)))
        self.entry_min_bath.pack(pady=(0, 10), fill='x', padx=10)

        self.label_aspect = ctk.CTkLabel(self.scroll_frame, text=":حداکثر نسبت طول به عرض اتاق", font=(persian_font, 12))
        self.label_aspect.pack(pady=(5, 2), anchor='e', padx=10)
        self.entry_aspect = ctk.CTkEntry(self.scroll_frame, justify='right')
        aspect_value = self.settings.get('aspect_ratio_limit', DEFAULT_ASPECT_RATIO_LIMIT)
        aspect_str = str(aspect_value)
        self.entry_aspect.insert(0, aspect_str)
        self.entry_aspect.pack(pady=(0, 15), fill='x', padx=10)

        # --- Drawing Settings ---
        draw_label = ctk.CTkLabel(self.scroll_frame, text="تنظیمات ترسیم", font=(persian_font, 13, 'bold'), anchor='e')
        draw_label.pack(pady=(10, 10), anchor='e', padx=10)

        self.label_wall_scale = ctk.CTkLabel(self.scroll_frame, text=":مقیاس ضخامت دیوار خارجی", font=(persian_font, 12))
        self.label_wall_scale.pack(pady=(5, 2), anchor='e', padx=10)
        self.entry_wall_scale = ctk.CTkEntry(self.scroll_frame, justify='right')
        self.entry_wall_scale.insert(0, str(self.settings.get('wall_thickness_scale', DEFAULT_WALL_THICKNESS_SCALE)))
        self.entry_wall_scale.pack(pady=(0, 10), fill='x', padx=10)

        self.label_font_scale = ctk.CTkLabel(self.scroll_frame, text=":مقیاس اندازه فونت برچسب", font=(persian_font, 12))
        self.label_font_scale.pack(pady=(5, 2), anchor='e', padx=10)
        self.entry_font_scale = ctk.CTkEntry(self.scroll_frame, justify='right')
        self.entry_font_scale.insert(0, str(self.settings.get('label_font_size_scale', DEFAULT_LABEL_FONT_SIZE_SCALE)))
        self.entry_font_scale.pack(pady=(0, 15), fill='x', padx=10)

        # --- Appearance Settings ---
        app_label = ctk.CTkLabel(self.scroll_frame, text="تنظیمات ظاهری", font=(persian_font, 13, 'bold'), anchor='e')
        app_label.pack(pady=(10, 10), anchor='e', padx=10)

        self.label_appearance = ctk.CTkLabel(self.scroll_frame, text=":حالت نمایش", font=(persian_font, 12))
        self.label_appearance.pack(pady=(5, 2), anchor='e', padx=10)
        self.appearance_menu = ctk.CTkOptionMenu(self.scroll_frame, values=["Light", "Dark", "System"],
                                                 command=self.apply_appearance_mode, font=(persian_font, 11)) # Apply immediately
        current_mode = self.settings.get('appearance_mode', 'System')
        self.appearance_menu.set(current_mode)
        self.appearance_menu.pack(pady=(0, 10), fill='x', padx=10)

        self.label_theme = ctk.CTkLabel(self.scroll_frame, text=":تم رنگی", font=(persian_font, 12))
        self.label_theme.pack(pady=(5, 2), anchor='e', padx=10)
        self.theme_menu = ctk.CTkOptionMenu(self.scroll_frame, values=["blue", "green", "dark-blue"],
                                            command=self.apply_color_theme, font=(persian_font, 11)) # Apply immediately
        self.theme_menu.set(self.settings.get('color_theme', 'blue'))
        self.theme_menu.pack(pady=(0, 20), fill='x', padx=10)


        # --- Buttons ---
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent") # Place buttons outside scroll frame
        self.button_frame.pack(pady=(5,10), fill='x', padx=10)

        self.save_button = ctk.CTkButton(self.button_frame, text="ذخیره تنظیمات", command=self.save_settings, font=(persian_font, 12))
        self.save_button.pack(side='right', padx=5)

        self.close_button = ctk.CTkButton(self.button_frame, text="بستن", command=self.close_dialog, fg_color="gray", font=(persian_font, 12))
        self.close_button.pack(side='right', padx=5)

    def apply_appearance_mode(self, mode):
        """Applies appearance mode immediately."""
        try:
            ctk.set_appearance_mode(mode)
            self.settings['appearance_mode'] = mode # Update setting immediately
        except Exception as e:
            print(f"Error applying appearance mode: {e}")

    def apply_color_theme(self, theme):
        """Applies color theme immediately."""
        try:
            # Theme change might require restart in some CTk versions/themes
            ctk.set_default_color_theme(theme)
            self.settings['color_theme'] = theme # Update setting immediately
            self.parent.set_status("تغییر تم ممکن است نیاز به راه‌اندازی مجدد داشته باشد.", color="orange", clear_after=7)
            # Force redraw? Might not work perfectly for theme.
            # self.parent.update()
            # self.parent.generate_and_display_plans() # Redraw plans might help update some colors
        except Exception as e:
            print(f"Error applying color theme: {e}")


    def save_settings(self):
        """Saves only the dimension and drawing settings."""
        try:
            # Save Dimension Settings
            min_room = float(self.entry_min_room.get())
            min_bath = float(self.entry_min_bath.get())
            aspect = float(self.entry_aspect.get())
            wall_scale = float(self.entry_wall_scale.get())
            font_scale = float(self.entry_font_scale.get())


            if not (1.0 <= min_room <= 5.0): raise ValueError("ابعاد اتاق اصلی باید بین 1 و 5 باشد")
            if not (0.8 <= min_bath <= 3.0): raise ValueError("ابعاد سرویس باید بین 0.8 و 3 باشد")
            if not (1.5 <= aspect <= 5.0): raise ValueError("نسبت ابعاد باید بین 1.5 و 5 باشد")
            if not (0.005 <= wall_scale <= 0.05): raise ValueError("مقیاس ضخامت دیوار باید بین 0.005 و 0.05 باشد")
            if not (0.01 <= font_scale <= 0.05): raise ValueError("مقیاس فونت برچسب باید بین 0.01 و 0.05 باشد")


            self.settings['min_room_dim'] = min_room
            self.settings['min_bath_dim'] = min_bath
            self.settings['min_stor_balc_dim'] = max(1.0, min_bath * 0.7)
            self.settings['aspect_ratio_limit'] = aspect
            self.settings['wall_thickness_scale'] = wall_scale
            self.settings['label_font_size_scale'] = font_scale

            # Appearance settings are applied immediately via menu commands

            self.parent.update_app_settings(self.settings) # Call parent method to update and regenerate
            # Keep the dialog open after saving
            self.parent.set_status("تنظیمات ابعاد و ترسیم ذخیره شد. نقشه‌ها دوباره تولید شدند.", color="green", clear_after=5)


        except ValueError as e:
            messagebox.showerror("خطای ورودی", f"مقدار نامعتبر است: {e}", parent=self)
        except Exception as e:
             messagebox.showerror("خطا", f"خطای ناشناخته: {e}", parent=self)

    def close_dialog(self):
        """Closes the settings dialog."""
        self.parent.settings_window = None # Inform parent that window is closed
        self.destroy()


class HousePlanApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("مولد نقشه خانه")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        initial_width = min(1100, int(screen_width * 0.7))
        initial_height = min(800, int(screen_height * 0.7))
        self.geometry(f"{initial_width}x{initial_height}")
        self.minsize(700, 500)

        # Hide main window initially
        self.withdraw()

        # Use a consistent Persian font if available
        self.persian_font = "Tahoma" if sys.platform == "win32" else "Arial" # Fallback

        # --- App Settings ---
        self.app_settings = {
            'min_room_dim': DEFAULT_MIN_ROOM_DIM,
            'min_bath_dim': DEFAULT_MIN_BATH_DIM,
            'min_stor_balc_dim': DEFAULT_MIN_STOR_BALC_DIM,
            'aspect_ratio_limit': DEFAULT_ASPECT_RATIO_LIMIT,
            'wall_thickness_scale': DEFAULT_WALL_THICKNESS_SCALE,
            'label_font_size_scale': DEFAULT_LABEL_FONT_SIZE_SCALE,
            'appearance_mode': ctk.get_appearance_mode(), # Store initial mode
            'color_theme': "blue" # Default theme
        }
        self.settings_window = None # To track if settings window is open

        # --- Top Frame (Inputs & Buttons) ---
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(pady=10, padx=20, fill="x")

        # Configure columns for RTL
        self.top_frame.columnconfigure(0, weight=0) # Button Help
        self.top_frame.columnconfigure(1, weight=0) # Button Settings
        self.top_frame.columnconfigure(2, weight=1) # Spacer
        self.top_frame.columnconfigure(3, weight=0) # Entry Length
        self.top_frame.columnconfigure(4, weight=0) # Label Length
        self.top_frame.columnconfigure(5, weight=0) # Entry Width
        self.top_frame.columnconfigure(6, weight=0) # Label Width
        self.top_frame.columnconfigure(7, weight=0) # Button Generate

        # --- Widgets (Added RTL order) ---
        self.generate_button = ctk.CTkButton(self.top_frame, text="تولید نقشه ها", width=120, command=self.generate_and_display_plans, font=(self.persian_font, 12))
        self.generate_button.grid(row=0, column=7, rowspan=2, padx=(10, 0), pady=10, sticky="ns")

        self.label_width = ctk.CTkLabel(self.top_frame, text=":عرض (متر)", font=(self.persian_font, 12))
        self.label_width.grid(row=0, column=6, padx=(5, 10), pady=(10,5), sticky="e")
        self.entry_width = ctk.CTkEntry(self.top_frame, placeholder_text="مثال: 10.5", width=80, justify='right')
        self.entry_width.grid(row=0, column=5, padx=(0, 5), pady=(10,5), sticky="e")
        self.entry_width.bind("<Return>", lambda event: self.entry_length.focus_set())

        self.label_length = ctk.CTkLabel(self.top_frame, text=":طول (متر)", font=(self.persian_font, 12))
        self.label_length.grid(row=1, column=6, padx=(5, 10), pady=(5,10), sticky="e")
        self.entry_length = ctk.CTkEntry(self.top_frame, placeholder_text="مثال: 15.0", width=80, justify='right')
        self.entry_length.grid(row=1, column=5, padx=(0, 5), pady=(5,10), sticky="e")
        self.entry_length.bind("<Return>", lambda event: self.generate_and_display_plans())

        # Settings and Help Buttons
        self.settings_button = ctk.CTkButton(self.top_frame, text="تنظیمات", width=80, fg_color="grey", command=self.show_settings_dialog, font=(self.persian_font, 12))
        self.settings_button.grid(row=0, column=1, rowspan=2, padx=(5, 5), pady=10, sticky="ns")

        self.help_button = ctk.CTkButton(self.top_frame, text="راهنما", width=80, fg_color="grey", command=self.show_help, font=(self.persian_font, 12))
        self.help_button.grid(row=0, column=0, rowspan=2, padx=(0, 5), pady=10, sticky="ns")


        # --- Status Label ---
        self.status_label = ctk.CTkLabel(self, text="لطفا ابعاد خانه را وارد کرده و دکمه تولید را بزنید.", text_color="gray", anchor='e', font=(self.persian_font, 11))
        self.status_label.pack(pady=(0, 5), padx=20, fill="x")


        # --- Tab View for Plans ---
        self.tab_view = ctk.CTkTabview(self, anchor="ne")
        self.tab_view.pack(pady=10, padx=20, fill="both", expand=True)

        self.plan_tabs = []
        self.plan_canvases = []
        # Create only 3 tabs
        self.num_plans = 3
        for i in range(self.num_plans):
            tab_name = f"نقشه {i+1}"
            tab = self.tab_view.add(tab_name)
            self.plan_tabs.append(tab)
            canvas = tk.Canvas(tab, bg="white", highlightthickness=0)
            canvas.pack(fill="both", expand=True, padx=1, pady=1)
            self.plan_canvases.append(canvas)
            canvas.bind("<Configure>", lambda event, c=canvas, idx=i: self.schedule_redraw(c, idx))

        self.current_plans = [[] for _ in range(self.num_plans)] # Adjust list size
        self.current_dimensions = (0, 0)
        self._redraw_jobs = [None] * self.num_plans # Adjust list size
        self._status_clear_job = None

        # Show Welcome Screen after main window is set up but hidden
        self.show_welcome_screen()


    def show_welcome_screen(self):
        welcome = WelcomeScreen(self)
        # Main loop continues, welcome screen handles showing the main window

    def set_status(self, message, color="gray", clear_after=0):
        """Updates the status label."""
        if self._status_clear_job:
             self.after_cancel(self._status_clear_job)
             self._status_clear_job = None
        self.status_label.configure(text=message, text_color=color)
        if clear_after > 0:
            self._status_clear_job = self.after(clear_after * 1000, lambda: self.status_label.configure(text=""))

    def update_app_settings(self, new_settings):
        """Callback from SettingsDialog to update main app settings and apply appearance."""
        self.app_settings = new_settings
        print("App settings updated:", self.app_settings)

        # Apply Appearance Settings immediately if they changed
        try:
            new_mode = self.app_settings.get('appearance_mode', 'System')
            new_theme = self.app_settings.get('color_theme', 'blue')
            if ctk.get_appearance_mode() != new_mode:
                 ctk.set_appearance_mode(new_mode)
            # Theme change might still require restart
            ctk.set_default_color_theme(new_theme)
            self.set_status("تنظیمات ذخیره شد. تغییر تم ممکن است نیاز به راه‌اندازی مجدد داشته باشد.", color="green", clear_after=7)
        except Exception as e:
            print(f"Error applying appearance settings: {e}")
            self.set_status("خطا در اعمال تنظیمات ظاهری.", color="orange", clear_after=5)

        # Regenerate plans with new dimension/drawing settings immediately if dimensions exist
        if self.current_dimensions[0] > 0 and self.current_dimensions[1] > 0:
             self.generate_and_display_plans() # Regenerate to reflect new settings

    def show_settings_dialog(self):
        """Opens the settings dialog, ensuring only one instance exists."""
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsDialog(self, self.app_settings)
            self.settings_window.focus()
        else:
            self.settings_window.focus() # Bring existing window to front


    def show_help(self):
        """Displays a help message box."""
        help_text = """
راهنمای مولد نقشه خانه:

۱. ابعاد خانه: طول و عرض مورد نظر خانه را به متر در کادرهای مربوطه وارد کنید.
۲. تولید نقشه‌ها: روی دکمه "تولید نقشه‌ها" کلیک کنید.
۳. مشاهده نقشه‌ها: برنامه ۳ طرح پیشنهادی مختلف را در تب‌های "نقشه ۱" تا "نقشه ۳" نمایش می‌دهد.

   - نقشه ۱: تقسیم‌بندی ساده فضا.
   - نقشه ۲: طرح با فضای نشیمن/آشپزخانه باز.
   - نقشه ۳: طرح L شکل برای نشیمن.

۴. تنظیمات: با کلیک روی دکمه "تنظیمات" می‌توانید حداقل ابعاد قابل قبول برای اتاق‌ها، حداکثر نسبت طول به عرض، مقیاس ضخامت دیوار، مقیاس فونت برچسب، حالت نمایش (روشن/تیره) و تم رنگی برنامه را تغییر دهید. تنظیمات ابعادی و ترسیم بر روی نقشه‌های بعدی که تولید می‌کنید تاثیر می‌گذارد.

نکته: نقشه‌های تولید شده صرفاً پیشنهادی و شماتیک هستند. رنگ‌ها برای تفکیک بهتر فضاها استفاده شده‌اند.
"""
        help_win = ctk.CTkToplevel(self)
        help_win.transient(self)
        help_win.grab_set()
        help_win.title("راهنما")
        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        help_win.geometry(f"500x520+{parent_x + parent_w // 2 - 250}+{parent_y + parent_h // 2 - 260}") # Increased height

        help_label = ctk.CTkLabel(help_win, text=help_text, justify="right", anchor="ne", font=(self.persian_font, 12), wraplength=460)
        help_label.pack(pady=20, padx=20, fill="both", expand=True)

        close_button = ctk.CTkButton(help_win, text="بستن", command=help_win.destroy, font=(self.persian_font, 12))
        close_button.pack(pady=10)

    def generate_and_display_plans(self):
        """Gets input, generates plans using current settings, and displays them."""
        self.set_status("در حال تولید نقشه‌ها...", color="blue")
        self.update_idletasks()

        try:
            width_str = self.entry_width.get()
            length_str = self.entry_length.get()
            if not width_str or not length_str:
                self.set_status("خطا: لطفا طول و عرض را وارد کنید.", color="orange", clear_after=5)
                return
            width = float(width_str)
            length = float(length_str)
            if width <= 0 or length <= 0:
                 self.set_status("خطا: طول و عرض باید مثبت باشند.", color="orange", clear_after=5)
                 return

            min_dim_req = self.app_settings['min_room_dim'] * 1.5
            if width < min_dim_req or length < min_dim_req:
                 self.set_status(f"هشدار: ابعاد کوچک است (حداقل ~{min_dim_req:.1f} متر توصیه می شود).", color="#FFA500", clear_after=10)

            print(f"\n=== Generating plans for {width}m x {length}m with settings: {self.app_settings} ===")
            self.current_dimensions = (width, length)
            # Generate only 3 plans
            self.current_plans = generate_plans(width, length, self.app_settings)
            print(f"=== Plan generation complete. Received {len(self.current_plans)} layouts. ===")

            self.update_idletasks()
            success_count = 0
            # Loop through the 3 canvases/plans
            for i in range(self.num_plans):
                if i < len(self.current_plans) and i < len(self.plan_canvases): # Ensure indices are valid
                    plan_data = self.current_plans[i]
                    canvas = self.plan_canvases[i]
                    if canvas.winfo_width() > 1 and canvas.winfo_height() > 1:
                         # Pass current settings to draw_plan
                         draw_plan(canvas, plan_data, width, length, self.app_settings)
                         success_count += 1
                    else:
                         print(f"Skipping draw for plan {i+1}: Canvas not ready ({canvas.winfo_width()}x{canvas.winfo_height()}). Scheduling redraw.")
                         self.schedule_redraw(canvas, i, delay=150)

            if success_count == self.num_plans:
                 self.set_status(f"آماده شد: {self.num_plans} نقشه برای {width}m x {length}m تولید شد.", color="green", clear_after=10)
            else:
                 self.set_status(f"هشدار: {success_count}/{self.num_plans} نقشه ترسیم شد. برخی نیاز به تغییر اندازه پنجره دارند.", color="orange", clear_after=10)

        except ValueError:
            self.set_status("خطای ورودی: لطفا اعداد معتبر برای طول و عرض وارد کنید.", color="red", clear_after=5)
            traceback.print_exc()
        except Exception as e:
            self.set_status(f"خطای غیرمنتظره در تولید نقشه: {e}", color="red", clear_after=10)
            print(f"Error during generation/display: {e}")
            traceback.print_exc()


    def schedule_redraw(self, canvas, index, delay=150):
        """Schedules a redraw for a specific canvas after a delay."""
        if index < len(self._redraw_jobs) and self._redraw_jobs[index]:
            self.after_cancel(self._redraw_jobs[index])
            self._redraw_jobs[index] = None
        if index < len(self._redraw_jobs):
            self._redraw_jobs[index] = self.after(delay, lambda c=canvas, idx=index: self.redraw_plan_if_needed(c, idx))

    def redraw_plan_if_needed(self, canvas, index):
        """Redraws a specific plan if dimensions and data are valid."""
        if index < len(self._redraw_jobs): self._redraw_jobs[index] = None
        # Check against num_plans
        if index < self.num_plans and index < len(self.current_plans) and self.current_dimensions[0] > 0:
            plan_data = self.current_plans[index]
            width, length = self.current_dimensions
            if canvas.winfo_exists() and canvas.winfo_width() > 1 and canvas.winfo_height() > 1:
                try:
                    # Pass current settings to draw_plan
                    draw_plan(canvas, plan_data, width, length, self.app_settings)
                except Exception as e:
                     print(f"Error during redraw of plan {index+1}: {e}")
                     traceback.print_exc()
                     try:
                         canvas.delete("all")
                         canvas.create_text(canvas.winfo_width()/2, canvas.winfo_height()/2, text=f"خطا در رسم نقشه {index+1}", fill="red", font=(self.persian_font, 12))
                     except: pass
        

if __name__ == "__main__":
    try: import PIL; print("Pillow library found.")
    except ImportError: print("Warning: Pillow library not found (pip install Pillow)")

    app = HousePlanApp()
    app.mainloop()
