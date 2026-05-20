import os
import struct

# إعدادات الألوان (RGB565 - Big Endian لأن الشاشة بتستخدم هاد النظام)
WHITE = 0xFFFF
BLACK = 0x0000

def set_pixel(data, x, y, color, width=240):
    """دالة لرسم بكسل واحد داخل مصفوفة البايتات"""
    # كل بكسل بياخذ 2 بايت
    index = (y * width + x) * 2
    # التعبئة بنظام Big-Endian (>H) المتوافق مع شاشات ST7789
    struct.pack_into('>H', data, index, color)

def process_bin_file(filepath):
    # قراءة الملف الأصلي
    with open(filepath, 'rb') as f:
        file_data = bytearray(f.read())
    
    # التأكد إن الملف حجمه صح (240 * 240 * 2 = 115200 بايت)
    if len(file_data) != 115200:
        print(f"تخطي الملف {filepath} (حجمه غير مطابق لشاشة 240x240)")
        return

    # --- إحداثيات وأبعاد البطارية ---
    start_x = 2
    start_y = 2
    bat_w = 22 # عرض جسم البطارية
    bat_h = 12 # ارتفاع البطارية
    
    # 1. تعبئة منطقة البطارية بالكامل باللون الأبيض (الخلفية)
    # بنعبي منطقة 24x12 (الجسم + البوز)
    for y in range(start_y, start_y + bat_h):
        for x in range(start_x, start_x + bat_w + 2):
            set_pixel(file_data, x, y, WHITE)

    # 2. رسم الإطار الأسود لجسم البطارية
    for x in range(start_x, start_x + bat_w):
        set_pixel(file_data, x, start_y, BLACK)              # الخط العلوي
        set_pixel(file_data, x, start_y + bat_h - 1, BLACK)  # الخط السفلي
        
    for y in range(start_y, start_y + bat_h):
        set_pixel(file_data, start_x, y, BLACK)              # الخط الأيسر
        set_pixel(file_data, start_x + bat_w - 1, y, BLACK)  # الخط الأيمن

    # 3. رسم القطب الموجب (البوز) باللون الأسود
    tip_y_start = start_y + 3
    tip_h = 6
    for y in range(tip_y_start, tip_y_start + tip_h):
        set_pixel(file_data, start_x + bat_w, y, BLACK)
        set_pixel(file_data, start_x + bat_w + 1, y, BLACK)

    # حفظ الملف الجديد باسم مختلف
    new_filepath = filepath.replace('.bin', '_bat.bin')
    with open(new_filepath, 'wb') as f:
        f.write(file_data)
    
    print(f"تمت إضافة البطارية بنجاح: {new_filepath}")

# --- تشغيل الكود على كل ملفات الـ bin في المجلد ---
print("بدأ معالجة الملفات...")
current_folder = os.getcwd()

# فلترة ملفات الـ bin (وتجاهل الملفات اللي تعدلت سابقاً)
for filename in os.listdir(current_folder):
    if filename.endswith('.bin') and not filename.endswith('_bat.bin'):
        process_bin_file(filename)

print("انتهى الشغل! انقل ملفات الـ (_bat.bin) على الـ SD Card.")