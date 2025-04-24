import random
import math

# --- Constants ---
DEFAULT_MIN_ROOM_DIM = 2.5
DEFAULT_MIN_BATH_DIM = 1.8
DEFAULT_MIN_STOR_BALC_DIM = 1.2
DEFAULT_ASPECT_RATIO_LIMIT = 3.0
# New defaults for drawing settings
DEFAULT_WALL_THICKNESS_SCALE = 0.01
DEFAULT_LABEL_FONT_SIZE_SCALE = 0.025


# --- Room Proportions ---
# General proportions for the remaining plans
PROPORTIONS_GENERAL = {
    "Living Room": 0.20,
    "Kitchen": 0.10,
    "Dining Area": 0.08, # Kept for simple split, ignored elsewhere
    "Master Bedroom": 0.15,
    "Bedroom 2": 0.12,
    "Bedroom 3": 0.10, # Optional
    "Bathroom": 0.05,
    "Balcony": 0.04, # Changed from Bathroom 2 to Balcony
    "Hallway/Corridor": 0.10,
    "Utility/Storage": 0.03,
}

# --- Color Mapping (Consistent) ---
ROOM_COLORS = {
    "Living Room": "#AED6F1",       # پذیرایی / نشیمن
    "Kitchen": "#FAD7A0",           # آشپزخانه
    "Master Bedroom": "#D8BFD8",    # اتاق خواب اصلی
    "Bedroom": "#FFDAB9",           # اتاق خواب (عمومی)
    "Bathroom": "#E6E6FA",          # حمام / سرویس
    "Hallway/Corridor": "#AED6F1",  # راهرو (همان رنگ پذیرایی)
    "Storage": "#D5DBDB",           # انباری
    "Utility": "#D5DBDB",           # تاسیسات / کاربردی
    "Balcony": "#C8E6C9",           # بالکن
    "Dining Area": "#ABEBC6",       # ناهارخوری
    "Unallocated": "#F0F0F0",       # تخصیص نیافته
    "Error": "#FFCCCC"              # خطا
}

# Persian names mapping for consistency in generation logic
PERSIAN_NAMES = {
    "Living Room": "پذیرایی",
    "Kitchen": "آشپزخانه",
    "Master Bedroom": "اتاق خواب اصلی",
    "Bedroom": "اتاق خواب", # Base name for others
    "Bathroom": "حمام", # Changed from base name
    "Hallway/Corridor": "راهرو",
    "Storage": "انباری",
    "Utility": "کاربردی",
    "Balcony": "بالکن",
    "Dining Area": "ناهارخوری",
    "Unallocated": "فضای باقیمانده",
    "Error": "خطا"
}


def _get_room_color(name):
    """Gets the color for a room name using consistent keys."""
    name_lower = name.lower()
    # Prioritize specific types by checking for keywords
    if "balcony" in name_lower or "بالکن" in name: return ROOM_COLORS["Balcony"]
    if "storage" in name_lower or "utility" in name_lower or "انباری" in name or "کاربردی" in name: return ROOM_COLORS["Storage"]
    if "bathroom" in name_lower or "service" in name_lower or "حمام" in name or "سرویس" in name: return ROOM_COLORS["Bathroom"]
    if "master bedroom" in name_lower or "اصلی" in name: return ROOM_COLORS["Master Bedroom"]
    if "bedroom" in name_lower or "اتاق خواب" in name: return ROOM_COLORS["Bedroom"] # General bedroom
    if "kitchen" in name_lower or "آشپزخانه" in name: return ROOM_COLORS["Kitchen"]
    if "living" in name_lower or "پذیرایی" in name: return ROOM_COLORS["Living Room"]
    if "dining" in name_lower or "ناهارخوری" in name: return ROOM_COLORS["Dining Area"]
    if "hallway" in name_lower or "corridor" in name_lower or "راهرو" in name: return ROOM_COLORS["Living Room"]  # Same as living room
    if "error" in name_lower or "خطا" in name: return ROOM_COLORS["Error"]
    if "unallocated" in name_lower or "باقیمانده" in name: return ROOM_COLORS["Unallocated"]

    for key, color in ROOM_COLORS.items():
        if key.lower() in name_lower:
            return color
    return ROOM_COLORS["Unallocated"]


class Rect:
    """Helper class for representing rectangular areas."""
    def __init__(self, x, y, w, h):
        self.x = float(x)
        self.y = float(y)
        self.w = max(0, float(w))
        self.h = max(0, float(h))
        self.area = self.w * self.h

    def intersects(self, other):
        if self.w <= 0 or self.h <= 0 or other.w <= 0 or other.h <= 0: return False
        return not (self.x + self.w <= other.x or other.x + other.w <= self.x or
                    self.y + self.h <= other.y or other.y + other.h <= self.y)

    def contains(self, other):
         if self.w <= 0 or self.h <= 0 or other.w <= 0 or other.h <= 0: return False
         return (self.x <= other.x and self.y <= other.y and
                 self.x + self.w >= other.x + other.w and
                 self.y + self.h >= other.y + other.h)

    def split_horizontal(self, split_h):
        """Splits the rectangle horizontally. Returns two Rects or None, None."""
        split_h = float(split_h)
        if 0 < split_h < self.h:
            h1 = max(0, split_h)
            h2 = max(0, self.h - split_h)
            if h1 > 1e-6 and h2 > 1e-6:
                 r1 = Rect(self.x, self.y, self.w, h1)
                 r2 = Rect(self.x, self.y + split_h, self.w, h2)
                 return r1, r2
        return None, None

    def split_vertical(self, split_w):
        """Splits the rectangle vertically. Returns two Rects or None, None."""
        split_w = float(split_w)
        if 0 < split_w < self.w:
            w1 = max(0, split_w)
            w2 = max(0, self.w - split_w)
            if w1 > 1e-6 and w2 > 1e-6:
                 r1 = Rect(self.x, self.y, w1, self.h)
                 r2 = Rect(self.x + split_w, self.y, w2, self.h)
                 return r1, r2
        return None, None

    def is_valid(self, min_dim=0.1):
        """Checks if width and height are above a minimum threshold."""
        return self.w >= min_dim and self.h >= min_dim

    def aspect_ratio(self):
        """Calculates aspect ratio (largest_dim / smallest_dim)."""
        if self.w <= 1e-6 or self.h <= 1e-6: return float('inf')
        return max(self.w / self.h, self.h / self.w)

    def __repr__(self):
        return f"Rect(x={self.x:.2f}, y={self.y:.2f}, w={self.w:.2f}, h={self.h:.2f})"

# --- Helper Functions ---
def check_room_validity(room_dict, settings):
    """Checks if a room dict has a valid rect based on settings."""
    rect = room_dict.get('rect')
    name = room_dict.get('name', 'Unknown')
    if not rect or not isinstance(rect, Rect): return False

    min_w, min_h = settings['min_room_dim'], settings['min_room_dim']
    name_lower = name.lower()
    # Use keywords for checking type
    if "bathroom" in name_lower or "service" in name_lower or "حمام" in name or "سرویس" in name:
        min_w, min_h = settings['min_bath_dim'], settings['min_bath_dim']
    elif "storage" in name_lower or "balcony" in name_lower or "utility" in name_lower or "انباری" in name or "بالکن" in name or "کاربردی" in name:
        min_w, min_h = settings['min_stor_balc_dim'], settings['min_stor_balc_dim']
    elif "hallway" in name_lower or "corridor" in name_lower or "راهرو" in name:
        min_w = settings['min_room_dim'] * 0.5 # Allow narrower hallway
    elif "unallocated" in name_lower or "باقیمانده" in name:
         min_w, min_h = settings['min_stor_balc_dim'] * 0.8, settings['min_stor_balc_dim'] * 0.8 # Allow smaller unallocated

    # Check dimensions with tolerance
    if not (rect.w >= min_w * 0.9 and rect.h >= min_h * 0.9):
        return False

    # Check aspect ratio (be more lenient for unallocated space)
    aspect = rect.aspect_ratio()
    aspect_limit = settings['aspect_ratio_limit']
    if "unallocated" in name_lower or "باقیمانده" in name:
        aspect_limit *= 1.5 # Allow more extreme aspect ratio for leftover space
    if aspect > aspect_limit:
        return False

    return True

def add_room(room_list, name_key, rect, settings, suffix=""):
    """Adds a room to the list if its rect is valid, using Persian names."""
    persian_name = PERSIAN_NAMES.get(name_key, name_key) + suffix
    # اتاق خواب‌ها رنگ یکسان داشته باشن مثل نقشه ۱
    if "اتاق خواب" in persian_name:
        color = ROOM_COLORS["Bedroom"]
    else:
        color = _get_room_color(name_key)
    room = {'name': persian_name, 'rect': rect, 'color': color}
    if rect and check_room_validity(room, settings):
        room_list.append(room)
        return True
    return False


# --- Layout Generation Functions ---

def _generate_layout_simple_split(house_w, house_l, settings):
    rooms = []
    initial_rect = Rect(0, 0, house_w, house_l)
    if not initial_rect.is_valid(): return rooms

    try:
        # First split: Living area from private area (40% for living)
        split_w_1 = house_w * 0.4
        living_area, private_area = initial_rect.split_vertical(split_w_1)

        if living_area and private_area:
            # Split living area into living and kitchen
            split_h_1 = living_area.h * 0.7
            living_rect, kitchen_rect = living_area.split_horizontal(split_h_1)
            add_room(rooms, "Living Room", living_rect, settings)
            add_room(rooms, "Kitchen", kitchen_rect, settings)

            # Calculate required space for bedrooms and adjust number of rooms
            min_bedroom_size = settings['min_room_dim'] * 1.1  # Slightly larger than minimum
            max_bedrooms = 2  # Default number of bedrooms
            
            # Reduce number of bedrooms if space is limited
            if private_area.h * 0.55 < min_bedroom_size * 1.5:
                max_bedrooms = 1
            
            # Split private area into bedrooms and bathrooms with hallway in between
            split_h_2 = private_area.h * 0.55  # Bedrooms area
            split_h_3 = private_area.h * 0.15  # Hallway height
            
            bedrooms_area = Rect(private_area.x, private_area.y, private_area.w, split_h_2)
            hallway_area = Rect(private_area.x, private_area.y + split_h_2, private_area.w, split_h_3)
            bathrooms_area = Rect(private_area.x, private_area.y + split_h_2 + split_h_3, 
                                private_area.w, private_area.h - split_h_2 - split_h_3)

            # Split bedrooms area based on available space
            if bedrooms_area.is_valid():
                if max_bedrooms == 2:
                    split_w_2 = bedrooms_area.w * 0.5
                    bed1_rect, bed2_rect = bedrooms_area.split_vertical(split_w_2)
                    add_room(rooms, "Bedroom", bed1_rect, settings, suffix=" ۱")
                    add_room(rooms, "Bedroom", bed2_rect, settings, suffix=" ۲")
                else:
                    # Only one bedroom if space is limited
                    add_room(rooms, "Master Bedroom", bedrooms_area, settings)

            # Add horizontal hallway if space allows
            if hallway_area.h >= settings['min_room_dim'] * 0.5:
                add_room(rooms, "Hallway/Corridor", hallway_area, settings)

            # Split bathrooms area into two rooms (bathroom and balcony) if space allows
            if bathrooms_area.is_valid():
                if bathrooms_area.w * 0.5 >= settings['min_bath_dim']:
                    split_w_3 = bathrooms_area.w * 0.5
                    bath1_rect, bath2_rect = bathrooms_area.split_vertical(split_w_3)
                    add_room(rooms, "Bathroom", bath1_rect, settings)
                    add_room(rooms, "Balcony", bath2_rect, settings)
                else:
                    # Only bathroom if space is limited
                    add_room(rooms, "Bathroom", bathrooms_area, settings)

    except Exception as e:
        print(f"Error in simple split: {e}")
        add_room(rooms, "Error", initial_rect, settings)

    if not rooms and initial_rect.is_valid():
        add_room(rooms, "Unallocated", initial_rect, settings)
    return rooms

def _generate_layout_open_concept(house_w, house_l, settings):
    """ Modified open concept layout with equal bedrooms and bathrooms, plus hallway. """
    rooms = []
    initial_rect = Rect(0, 0, house_w, house_l)
    if not initial_rect.is_valid(): return rooms
    min_room_dim = settings['min_room_dim']

    # Decide orientation based on house dimensions
    open_ratio = 0.6
    if house_w > house_l * 1.2:  # Wide house
        open_w = house_w * open_ratio
        private_w = house_w - open_w
        open_rect = Rect(0, 0, open_w, house_l)
        private_rect = Rect(open_w, 0, private_w, house_l)
        is_wide = True
    else:  # Long house
        open_h = house_l * open_ratio
        private_h = house_l - open_h
        open_rect = Rect(0, 0, house_w, open_h)
        private_rect = Rect(0, open_h, house_w, private_h)
        is_wide = False

    # Split Open Area
    if open_rect.is_valid(min_room_dim * 0.8):
        k_ratio = 0.35
        if is_wide:
            k_h = open_rect.h * k_ratio
            k_rect, l_rect = open_rect.split_horizontal(k_h)
        else:
            k_w = open_rect.w * k_ratio
            k_rect, l_rect = open_rect.split_vertical(k_w)
        add_room(rooms, "Kitchen", k_rect, settings, suffix=" (باز)")
        add_room(rooms, "Living Room", l_rect, settings, suffix=" (باز)")
    elif open_rect.is_valid():
        add_room(rooms, "Unallocated", open_rect, settings, suffix=" (باز)")

    # Split Private Area
    if private_rect.is_valid(min_room_dim):
        # Split bedrooms and bathrooms first
        if is_wide:
            split_h = private_rect.h * 0.6
            bedrooms_area, bathrooms_area = private_rect.split_horizontal(split_h)
        else:
            split_w = private_rect.w * 0.6
            bedrooms_area, bathrooms_area = private_rect.split_vertical(split_w)

        if bedrooms_area and bathrooms_area:
            # Add hallway between bedrooms
            hallway_size = min(bedrooms_area.w * 0.15, settings['min_room_dim'] * 1.2)
            bed_area, hallway_rect = bedrooms_area.split_vertical(bedrooms_area.w - hallway_size)
            add_room(rooms, "Hallway/Corridor", hallway_rect, settings, suffix=" اتاق‌ها")

            # Split remaining bedroom area equally
            if bed_area:
                split_bed = bed_area.w * 0.5
                bed1_rect, bed2_rect = bed_area.split_vertical(split_bed)
                add_room(rooms, "Master Bedroom", bed1_rect, settings)
                add_room(rooms, "Bedroom", bed2_rect, settings, suffix=" ۲")

            # Add hallway between bathrooms
            bath_hallway_size = min(bathrooms_area.w * 0.15, settings['min_room_dim'] * 1.2)
            bath_area, bath_hallway_rect = bathrooms_area.split_vertical(bathrooms_area.w - bath_hallway_size)
            add_room(rooms, "Hallway/Corridor", bath_hallway_rect, settings, suffix=" سرویس‌ها")

            # Split remaining bathroom area (bathroom and balcony)
            if bath_area:
                split_bath = bath_area.w * 0.5
                bath1_rect, bath2_rect = bath_area.split_vertical(split_bath)
                add_room(rooms, "Bathroom", bath1_rect, settings)
                add_room(rooms, "Balcony", bath2_rect, settings)
    elif private_rect.is_valid():
        add_room(rooms, "Unallocated", private_rect, settings)

    return rooms

def _generate_layout_l_shape_living(house_w, house_l, settings):
    """Plan 3: Final version with large kitchen, full-length bathroom and mirrored balcony."""
    rooms = []
    rect = Rect(0, 0, house_w, house_l)
    if not rect.is_valid(): return rooms

    try:
        min_room = settings['min_room_dim']
        hallway_w = min(1.0, house_w * 0.15)

        # 1. فضای عمومی و خصوصی
        public_h = house_l * 0.4
        private_h = house_l - public_h
        public_area = Rect(0, 0, house_w, public_h)

        # 2. پذیرایی و آشپزخانه
        add_room(rooms, "Living Room", public_area, settings)

        kitchen_w = max(min_room, house_w * 0.4)
        kitchen_h = max(min_room, public_h * 0.4)
        kitchen_rect = Rect(0, 0, kitchen_w, kitchen_h)
        add_room(rooms, "Kitchen", kitchen_rect, settings)

        # 3. راهرو و تقسیم خصوصی
        hallway_h = private_h * 0.85
        hallway_x = (house_w - hallway_w) / 2
        hallway_rect = Rect(hallway_x, public_h, hallway_w, hallway_h)
        add_room(rooms, "Hallway/Corridor", hallway_rect, settings)

        side_w = (house_w - hallway_w) / 2
        bed_h = hallway_h * 0.7

        # اتاق خواب اصلی (چپ)
        bed1_rect = Rect(0, public_h, side_w, bed_h)
        master_ok = add_room(rooms, "Master Bedroom", bed1_rect, settings)

        # اتاق دوم (راست)
        bed2_rect = Rect(hallway_x + hallway_w, public_h, side_w, bed_h)
        second_ok = add_room(rooms, "Bedroom", bed2_rect, settings, suffix=" ۲")

        if not master_ok and second_ok:
            rooms[-1]["name"] = "اتاق خواب اصلی"

        # 4. سرویس بهداشتی - زیر اتاق خواب سمت چپ (کامل)
        bath_y = public_h + bed_h
        bath_h = private_h - bed_h
        bath_rect = Rect(0, bath_y, side_w, bath_h)
        add_room(rooms, "Bathroom", bath_rect, settings)

        # 5. بالکن - زیر اتاق خواب سمت راست (قرینه سرویس)
        balc_rect = Rect(hallway_x + hallway_w, bath_y, side_w, bath_h)
        add_room(rooms, "Balcony", balc_rect, settings)

    except Exception as e:
        print(f"Error in Plan 3: {e}")
        add_room(rooms, "Error", rect, settings)

    if not rooms:
        add_room(rooms, "Unallocated", rect, settings)

    return rooms





def generate_plans(width, length, settings):
    """
    Generates 3 different plan layouts based on house dimensions and settings.
    """
    num_plans_to_generate = 3
    min_dim_req = settings['min_room_dim'] * 1.5
    if width < min_dim_req or length < min_dim_req:
        print(f"Warning: House dimensions ({width}x{length}) are very small.")
        error_rect = Rect(0,0,width,length)
        error_room = {'name': PERSIAN_NAMES["Error"] + " - مساحت خیلی کوچک", 'rect': error_rect, 'color':_get_room_color('Error')}
        return [[error_room]] * num_plans_to_generate

    plans = []
    # Updated list of layout functions
    layout_functions = [
        _generate_layout_simple_split,
        _generate_layout_open_concept,
        _generate_layout_l_shape_living,
    ]

    for i, func in enumerate(layout_functions):
        plan_name = func.__name__.replace("_generate_layout_", "")
        print(f"\n--- Generating Plan {i+1} ({plan_name}) ---")
        try:
            plan = func(width, length, settings)
            # Final validation pass
            validated_plan = [room for room in plan if check_room_validity(room, settings)]

            if not validated_plan:
                 print(f"  Warning: Plan {i+1} resulted in no valid rooms after validation.")
                 validated_plan = [{'name': f'نقشه {i+1} {PERSIAN_NAMES["Error"]} - بدون اتاق معتبر', 'rect': Rect(0,0,width,length), 'color':_get_room_color('Error')}]
            plans.append(validated_plan)
            print(f"  Plan {i+1} generated with {len(validated_plan)} valid room(s).")

        except Exception as e:
            print(f"  ERROR generating Plan {i+1} ({plan_name}): {e}")
            import traceback
            traceback.print_exc()
            plans.append([{'name': f'نقشه {i+1} {PERSIAN_NAMES["Error"]} اجرایی', 'rect': Rect(0,0,width,length), 'color':_get_room_color('Error')}])

    # Final check
    for i, plan in enumerate(plans):
        if not plan:
             plans[i] = [{'name': f'نقشه {i+1} {PERSIAN_NAMES["Error"]} تولید ناموفق', 'rect': Rect(0,0,width,length), 'color':_get_room_color('Error')}]

    # Ensure exactly num_plans_to_generate plans are returned
    while len(plans) < num_plans_to_generate:
        plans.append([{'name': f'نقشه {len(plans)+1} {PERSIAN_NAMES["Error"]} تولید نشده', 'rect': Rect(0,0,width,length), 'color':_get_room_color('Error')}])

    return plans[:num_plans_to_generate] # Return only the required number