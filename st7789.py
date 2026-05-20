import time
from micropython import const
import ustruct as struct
import machine
import micropython
import math
import framebuf

# --- الثوابت والأوامر ---
ST77XX_SWRESET = const(0x01)
ST77XX_SLPOUT  = const(0x11)
ST77XX_NORON   = const(0x13)
ST77XX_INVON   = const(0x21)
ST77XX_DISPON  = const(0x29)
ST77XX_CASET   = const(0x2A)
ST77XX_RASET   = const(0x2B)
ST77XX_RAMWR   = const(0x2C)
ST77XX_COLMOD  = const(0x3A)
ST7789_MADCTL  = const(0x36)

BLACK   = const(0x0000)
WHITE   = const(0xFFFF)
RED     = const(0xF800)
GREEN   = const(0x07E0)
BLUE    = const(0x001F)
YELLOW  = const(0xFFE0)
CYAN    = const(0x07FF)
MAGENTA = const(0xF81F)

class ST7789:
    def __init__(self, spi, width, height, reset, dc, cs=None, backlight=None):
        self.width = width
        self.height = height
        self.spi = spi
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.backlight = backlight
        
        if self.cs: self.cs.init(machine.Pin.OUT, value=1)
        if self.dc: self.dc.init(machine.Pin.OUT, value=0)
        if self.reset: self.reset.init(machine.Pin.OUT, value=1)
        if self.backlight: self.backlight.init(machine.Pin.OUT, value=1)
        
        self.init_display()

    def write_cmd(self, cmd):
        if self.cs: self.cs(0)
        self.dc(0)
        self.spi.write(bytes([cmd]))
        if self.cs: self.cs(1)

    def write_data(self, buf):
        if self.cs: self.cs(0)
        self.dc(1)
        self.spi.write(buf)
        if self.cs: self.cs(1)

    def init_display(self):
        self.reset(1)
        time.sleep_ms(50)
        self.reset(0)
        time.sleep_ms(50)
        self.reset(1)
        time.sleep_ms(150)
        
        self.write_cmd(ST77XX_SWRESET)
        time.sleep_ms(150)
        self.write_cmd(ST77XX_SLPOUT)
        time.sleep_ms(255)
        self.write_cmd(ST77XX_COLMOD)
        self.write_data(b'\x55') 
        self.write_cmd(ST7789_MADCTL)
        self.write_data(b'\x00') 
        self.write_cmd(ST77XX_INVON)
        self.write_cmd(ST77XX_NORON)
        self.write_cmd(ST77XX_DISPON)

    def set_window(self, x0, y0, x1, y1):
        self.write_cmd(ST77XX_CASET)
        self.write_data(struct.pack(">HH", x0, x1))
        self.write_cmd(ST77XX_RASET)
        self.write_data(struct.pack(">HH", y0, y1))
        self.write_cmd(ST77XX_RAMWR)

    def fill_rect(self, x, y, w, h, color):
        """رسم سريع باستخدام كتل البيانات"""
        if x >= self.width or y >= self.height: return
        w = min(w, self.width - x)
        h = min(h, self.height - y)
        
        self.set_window(x, y, x + w - 1, y + h - 1)
        
        # نرسل البيانات بحزم كبيرة (4096 بايت)
        chunk_size = 4096 
        color_bin = struct.pack(">H", color)
        buffer = color_bin * (chunk_size // 2)
        
        total_bytes = w * h * 2
        chunks = total_bytes // chunk_size
        rest = total_bytes % chunk_size
        
        if self.cs: self.cs(0)
        self.dc(1)
        
        for _ in range(chunks):
            self.spi.write(buffer)
        if rest:
            self.spi.write(buffer[:rest])
            
        if self.cs: self.cs(1)

    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)

    def draw_image(self, filename, x, y, w, h):
        """
        رسم صورة من ملف .bin محفوظ في الذاكرة
        """
        try:
            f = open(filename, 'rb')
        except OSError:
            print("File not found:", filename)
            return

        self.set_window(x, y, x + w - 1, y + h - 1)
        
        # نقرأ 1024 بايت في كل مرة لتوفير الرام
        chunk_size = 1024 
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            self.write_data(data)
        
        f.close()
    
    
    # --- دالة النص السريعة (بدون native وبدون framebuf) ---
    @micropython.native
    def text(self, font, s, x, y, color, bg=BLACK):

        f_width = font.WIDTH
        f_height = font.HEIGHT
        
        # 1. تجهيز مصفوفة بحجم الحرف الواحد
        bytes_per_char = f_width * f_height * 2
        char_buffer = bytearray(bytes_per_char)
        
        # 2. تقسيم الألوان لتسريع العملية
        color_high = (color >> 8) & 0xFF
        color_low = color & 0xFF
        bg_high = (bg >> 8) & 0xFF
        bg_low = bg & 0xFF
        
        bytes_per_row = (f_width + 7) // 8

        # 3. المرور على كل حرف ورسمه في الذاكرة ثم إرساله
        for char in s:
            ch_data = font.get_ch(char)
            idx = 0
            for row in range(f_height):
                for col in range(f_width):
                    # حساب البت المطلوب
                    byte_index = (row * bytes_per_row) + (col // 8)
                    bit_index = 7 - (col % 8)
                    
                    if (ch_data[byte_index] >> bit_index) & 1:
                        char_buffer[idx] = color_high
                        char_buffer[idx+1] = color_low
                    else:
                        char_buffer[idx] = bg_high
                        char_buffer[idx+1] = bg_low
                    idx += 2
            
            # إرسال الحرف كاملاً للشاشة دفعة واحدة
            self.set_window(x, y, x + f_width - 1, y + f_height - 1)
            self.write_data(char_buffer)
            x += f_width



    # --- 3. رسم خط خميل (سماكة مخصصة) ---
    def thick_line(self, x0, y0, x1, y1, color, thickness=3):
        half = thickness // 2
        
        # إذا كان الخط أفقي تماماً
        if y0 == y1:
            self.fill_rect(min(x0, x1), y0 - half, abs(x1 - x0) + 1, thickness, color)
            return

        # إذا كان الخط عمودي تماماً
        if x0 == x1:
            self.fill_rect(x0 - half, min(y0, y1), thickness, abs(y1 - y0) + 1, color)
            return

        # للخطوط المائلة: ارسم عدة خطوط متوازية (أسرع من البكسل بكسل)
        dx = abs(x1 - x0); dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
        err = dx + dy
        
        while True:
            # بدل بكسل واحد، بنرسم "مربع" صغير يمثل السمك
            self.fill_rect(x0 - half, y0 - half, thickness, thickness, color)
            if x0 == x1 and y0 == y1: break
            e2 = 2 * err
            if e2 >= dy: err += dy; x0 += sx
            if e2 <= dx: err += dx; y0 += sy

    # 1. دالة رسم نقطة (مطلوبة للدائرة)
    def pixel(self, x, y, color):
        self.set_window(x, y, x, y)
        self.write_data(struct.pack(">H", color))

    def draw_fast_line(self, x1, y1, x2, y2, color, back, thickness=1):
        # 1. حساب أبعاد "الصندوق" الذي يحتوي الخط
        # بنحدد أصغر x وأكبر x، وأصغر y وأكبر y عشان نعرف وين الخط موجود
        min_x = min(x1, x2) - thickness
        max_x = max(x1, x2) + thickness
        min_y = min(y1, y2) - thickness
        max_y = max(y1, y2) + thickness

        # التأكد إننا ما طلعنا برا حدود الشاشة (Clipping)
        min_x = max(0, min_x)
        min_y = max(0, min_y)
        max_x = min(self.width, max_x)
        max_y = min(self.height, max_y)

        # 2. حساب عرض وطول الصندوق
        w_buf = max_x - min_x
        h_buf = max_y - min_y

        if w_buf <= 0 or h_buf <= 0: return # الخط برا الشاشة

        # 3. إنشاء الرام المؤقتة (Buffer) على قد الصندوق بس
        # المعادلة: العرض * الطول * 2 بايت
        buffer = bytearray(w_buf * h_buf * 2)
        fb = framebuf.FrameBuffer(buffer, w_buf, h_buf, framebuf.RGB565)

        # 4. تنظيف الرام باللون الأسود (أو لون خلفيتك)
        # ملاحظة: هون في مشكلة صغيرة رح اشرحها تحت (مشكلة الخلفية السوداء)
        fb.fill(back) 

        # 5. رسم الخط داخل الرام
        # لازم نطرح min_x و min_y عشان نرسم بالنسبة لزاوية الصندوق (0,0)
        # السماكة بنعملها برسم خطوط جنب بعض
        for i in range(-(thickness//2), (thickness//2) + 1):
             # معادلة الإزاحة لعمل السماكة
            fb.line(x1 - min_x + i, y1 - min_y, x2 - min_x + i, y2 - min_y, color)
            fb.line(x1 - min_x, y1 - min_y + i, x2 - min_x, y2 - min_y + i, color)

        # 6. إرسال الصندوق للشاشة في موقعه الصحيح
        self.set_window(min_x, min_y, min_x + w_buf - 1, min_y + h_buf - 1)
        self.write_data(buffer)

    def draw_number(self, num, x, y, color_txt, color_back, size=2):
        # استخدام framebuf الداخلي لرسم نص بسيط
        # size=2 سيقوم بمضاعفة الحجم
        string_num = str(num)
        # ملاحظة: framebuf الافتراضي في ميكروبايثون صغير (8x8)
        # هذه الطريقة سريعة جداً للأرقام
        self.fill_rect(x, y, len(string_num)*8*size, 8*size, color_back) # تنظيف مكان الرقم القديم
        
        # هنا نستخدم الـ FrameBuffer لرسم الخط وتكبيره
        temp_buf = bytearray(8 * len(string_num))
        fb = framebuf.FrameBuffer(temp_buf, 8 * len(string_num), 8, framebuf.MONO_VLSB)
        fb.text(string_num, 0, 0, 1)
        
        for ty in range(8):
            for tx in range(8 * len(string_num)):
                if fb.pixel(tx, ty):
                    self.fill_rect(x + tx*size, y + ty*size, size, size, color_txt)

    def fill_circle(self, x0, y0, r, color):
        """رسم دائرة ممتلئة بالألوان"""
        x = r
        y = 0
        err = 0

        while x >= y:
            # رسم خطوط أفقية بدلاً من نقاط مفردة لملء الدائرة
            self.thick_line(x0 - x, y0 + y, x0 + x, y0 + y, color, 1)
            self.thick_line(x0 - y, y0 + x, x0 + y, y0 + x, color, 1)
            self.thick_line(x0 - x, y0 - y, x0 + x, y0 - y, color, 1)
            self.thick_line(x0 - y, y0 - x, x0 + y, y0 - x, color, 1)

            y += 1
            if err <= 0:
                err += 2*y + 1
            else:
                x -= 1
                err += 2*(y - x) + 1

    # 2. دالة الدائرة (مع التحكم بالسماكة)
    def circle(self, x0, y0, r, color, thickness=1):
        # حلقة تكرار لرسم الدوائر فوق بعضها لتحقيق السماكة
        for i in range(thickness):
            radius = r - i
            if radius < 0: break
            
            f = 1 - radius
            ddF_x = 1
            ddF_y = -2 * radius
            x = 0
            y = radius
            
            self.pixel(x0, y0 + radius, color)
            self.pixel(x0, y0 - radius, color)
            self.pixel(x0 + radius, y0, color)
            self.pixel(x0 - radius, y0, color)
            
            while x < y:
                if f >= 0:
                    y -= 1
                    ddF_y += 2
                    f += ddF_y
                x += 1
                ddF_x += 2
                f += ddF_x
                
                self.pixel(x0 + x, y0 + y, color)
                self.pixel(x0 - x, y0 + y, color)
                self.pixel(x0 + x, y0 - y, color)
                self.pixel(x0 - x, y0 - y, color)
                self.pixel(x0 + y, y0 + x, color)
                self.pixel(x0 - y, y0 + x, color)
                self.pixel(x0 + y, y0 - x, color)
                self.pixel(x0 - y, y0 - x, color)

    def fill_triangle(self, x0, y0, x1, y1, x2, y2, color):
        """
        رسم مثلث ممتلئ باللون (Solid Triangle)
        """
        # ترتيب النقاط بحيث تكون y0 هي القمة (الأصغر) و y2 هي القاع (الأكبر)
        if y0 > y1: x0, x1 = x1, x0; y0, y1 = y1, y0
        if y1 > y2: x1, x2 = x2, x1; y1, y2 = y2, y1
        if y0 > y1: x0, x1 = x1, x0; y0, y1 = y1, y0

        if y0 == y2: return  # لا يوجد ارتفاع للرسم

        # حساب ميل الأضلاع
        # dx01 هو التغير في x لكل خطوة y للضلع الأول، وهكذا
        dx01 = 0 if y1 == y0 else (x1 - x0) / (y1 - y0)
        dx02 = 0 if y2 == y0 else (x2 - x0) / (y2 - y0)
        dx12 = 0 if y2 == y1 else (x2 - x1) / (y2 - y1)

        sa, sb = x0, x0 # sa: start x, sb: end x

        # الجزء العلوي من المثلث
        if y1 == y2: last = y1 # إذا كان المثلث مسطحاً من الأسفل
        else: last = y1 - 1

        for y in range(y0, last + 1):
            self.thick_line(int(sa), y, int(sb), y, color, 1)
            sa += dx01
            sb += dx02

        # الجزء السفلي من المثلث
        sa = x1
        sb = x0 + dx02 * (y1 - y0)
        
        for y in range(y1, y2 + 1):
            self.thick_line(int(sa), y, int(sb), y, color, 1)
            sa += dx12
            sb += dx02
    
    # --- الإضافة السحرية لتوفير الطاقة ---
    def sleep_mode(self, state):
        """تفعيل أو إيقاف وضع النوم العميق للشريحة لتوفير الطاقة"""
        if state:
            self.write_cmd(0x10) # أمر النوم (Sleep In)
            time.sleep_ms(150)
        else:
            self.write_cmd(0x11) # أمر الاستيقاظ (Sleep Out)
            time.sleep_ms(120)
   
    def update_battery_level(self, x, y, percentage, bg_inner_color=WHITE):
        """
        تحديث مستوى الشحن داخل هيكل البطارية المرسوم مسبقاً في التصميم
        x و y هي إحداثيات الزاوية العلوية اليسرى لهيكل البطارية (مثلاً 2, 2)
        """
        # 1. تحديد اللون
        if percentage > 65:
            fill_color = GREEN
        elif percentage > 40:
            fill_color = YELLOW
        else:
            fill_color = RED    
            
        # 2. مسح التعبئة القديمة (المنطقة الداخلية أبعادها 20x10 وتبدأ بعد الإطار ببكسل واحد)
        self.fill_rect(x + 1, y + 1, 20, 10, bg_inner_color)
        
        # 3. رسم التعبئة الجديدة
        fill_width = int((percentage / 100.0) * 20) # العرض الأقصى الداخلي هو 20 بكسل
        if fill_width > 0:
            self.fill_rect(x + 1, y + 1, fill_width, 10, fill_color)