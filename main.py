import _thread
from machine import I2C, Pin, SPI, PWM, RTC, lightsleep, ADC
import math
import time
import st7789
import sdcard
import os
import struct
import gc

print("delay, 3s")
time.sleep(3)

#_________compas_______________________
# --- 1. إعداد الاتصال ---
# QMC6310 Address = 0x2C (44)
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
ADDRESS = 0x2C 
#______________________________

# ----------------- إعدادات الشاشة -----------------
spi = SPI(1, baudrate=60000000, polarity=1, phase=1, sck=Pin(10), mosi=Pin(11))
tft = st7789.ST7789(spi, 240, 240, reset=Pin(12), dc=Pin(20), cs=Pin(19))
tft.fill(st7789.BLACK)

# ----------------- إعدادات SD Card -----------------
spi_sd = SPI(0, baudrate=5000000, polarity=0, phase=0, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cs = Pin(16, Pin.OUT)

try:
    sd = sdcard.SDCard(spi_sd, cs)
    vfs = os.VfsFat(sd) # type: ignore
    os.mount(vfs, "/sd")
except Exception as e:
    print("SD Mount Error (or already mounted):", e)

# ----------------- المتغيرات المشتركة (Global) -----------------
draw_me = None
job_data = None
# القيم الافتراضية
width = 240
height = 240 

#----اللوان ----------.
def swap_bytes(color):
    return ((color & 0xFF) << 8) | ((color >> 8) & 0xFF)
background_1 = swap_bytes(0x00E5) 
background = swap_bytes(0xFFDE)
camel = const(0x5160)
dark_green = const(0x01e5)

# تفعيل ساعة النظام الداخلية
rtc = RTC()


but_R = Pin(8,Pin.IN, Pin.PULL_DOWN)
but_L =Pin(13, Pin.IN, Pin.PULL_DOWN)
but_Down = Pin(7,Pin.IN, Pin.PULL_DOWN)
but_Up = Pin(9, Pin.IN, Pin.PULL_DOWN)

on_sys = Pin(17,Pin.IN, Pin.PULL_DOWN)

rjaj = Pin(6, Pin.OUT)
screen = Pin(14, Pin.OUT)


x = 0
g = 0
page = 0
clean_t = 0
sf7a = 0
count = 0
test_x = 0
test_y = 0
test_x1 = 0
test_y1 = 0
rsm_1 = 0
rsm_2 = 0
ms7 = 0
sys_on = 0
sys_off = 0
time_n = 0
second_back = 0
minute_back = 0
hour_back = 0
day_back = 1
month_back = 1
hour_check = 0
min_check = 0
sec_check = 0
t3del_clock1 = 0 
t3del_clock = 0
day_check = 1
mon_check = 1
hour_12 = 0 
found = []
numS = 0
numS1 = 50
ampm = "AM"
per_bat = 0
per_bat_check = 0 
f_color,d_color,asr_color,m_color,ash_color=0x0204,0x0204,0x0204,0x0204,0x0204
core1 = 0
sd_on = 1
sb7_33,sb7_33_2,no_sb7=0,0,0

try:
    with open('/sd/log_count.txt', 'r') as f:
        count_sb7 = int(f.read())
except Exception as e:
    try:
        with open('/sd/log_count.txt', 'w') as f:
            f.write("0")
            count_sb7 = 0
    except Exception as f:
        print(f)         
    print(e)

def get_prayer_time(day, month):
    search_date = f"{day}-{month}"
    try:
        with open("/sd/pray_time_jordan.csv", 'r') as f:
            for line in f:
                if line.startswith(search_date):
                    # نأخذ التاريخ والوقت فقط ونغلق الملف فوراً
                    row = line.strip().split(',')
                    return [row] # نرجع التاريخ والوقت (بدون العمود الثالث)
    except Exception as e:
        print("File error:", e)
    return ["N/A", "N/A"]

try:#سحب الوقت والساعة
    with open('log_clock.txt', 'r') as f:
        h, m, s, d, mo = str(f.read()).split(":")
        second_back = int(s)
        minute_back = int(m)
        hour_back = int(h)
        day_back = int(d)
        month_back = int(mo)
except Exception as e:
    with open('log_clock.txt', 'w') as f:
        f.write("0:0:0:1:1")
    print(e)

rtc.datetime((2026, month_back, day_back, 0, hour_back, minute_back, second_back, 0))#حتى تقول للساعة الداخلية غير توقيتك الى


#عشان تدور على الصلوات وتحسب اقرب صلاة
def row(day, month, hour, min):  
    try:
        found_row = get_prayer_time(int(day), int(month))
        found_row12cul = []
        found_row12show = []
        slah_num = 0
        for i in range (6):
            time_time = str(found_row[0][i+1]).split(":")

            found_row12cul.append(time_time) #نفصل كل اشي حتى يسهل حساب الارقام
            #time_time=["",""]

            if int(time_time[0]) > 12 : time_time12 = int(time_time[0]) - 12
            else: time_time12 = int(time_time[0])

            if time_time12 < 10 : time_time12 = f"0{time_time12}"

            found_row12show.append(f"{time_time12}:{time_time[1]}")#هاي رح نستخدمها للعرض

        for i in range(6):
            if (int(hour)-int(found_row12cul[i][0]))==0 and (int(min)-int(found_row12cul[i][1]))<0:
                slah_num=i
                break
            elif (int(hour)-int(found_row12cul[i][0]))<0:
                slah_num=i
                break


        return slah_num, found_row12show
    except Exception as e:
        print(e)
        return 0,0

numS,found = row(day_back,month_back,hour_back,minute_back)

#عشان تغير يلون اقرب صلاة
def slah_color(num,list,do):
    global f_color,d_color,asr_color,m_color,ash_color
    if do == "txt":#رسم الصلاة لوحدها
        if num == 0:
            tft.draw_number(list[0],196,222,st7789.RED,0xEEB7,size=1)
        elif num == 1 or num == 2:
            tft.draw_number(list[2],149,222,st7789.RED,0xEEB7,size=1)
        elif num == 3:
            tft.draw_number(list[3],103,222,st7789.RED,0xEEB7,size=1)
        elif num == 4:
            tft.draw_number(list[4],56,222,st7789.RED,0xEEB7,size=1)
        elif num == 5:
            tft.draw_number(list[5],7,222,st7789.RED,0xEEB7,size=1)  
    elif do == "color": #سحب اللون
        f_color,d_color,asr_color,m_color,ash_color=0x0204,0x0204,0x0204,0x0204,0x0204
        if num == 0:
            f_color = st7789.RED
        elif num == 1 or num == 2:
            d_color = st7789.RED
        elif num == 3:
            asr_color = st7789.RED
        elif num == 4:
            m_color = st7789.RED
        elif num == 5:
            ash_color = st7789.RED
                 
               
class BatteryMonitor:
    def __init__(self, pin_num):
        self.rc_pin = Pin(pin_num, Pin.IN, pull=None) # pyright: ignore[reportArgumentType]
        self.state = "IDLE"
        self.timer = 0
        self.percent = 100 # النسبة الافتراضية
        
        # أرقام المعايرة تبعتك
        self.TIME_FULL = 624
        self.TIME_EMPTY = 1200

    def update(self):
        now = time.ticks_ms()

        # 1. حالة السكون: بدء التفريغ
        if self.state == "IDLE":
            self.rc_pin.init(Pin.OUT)
            self.rc_pin.value(0)
            self.timer = now
            self.state = "DISCHARGING"

        # 2. حالة التفريغ: نشيك إذا مر ثانية بدون ما نوقف الكود
        elif self.state == "DISCHARGING":
            if time.ticks_diff(now, self.timer) >= 1000:
                self.rc_pin.init(Pin.IN, pull=None) # type: ignore
                self.timer = time.ticks_ms() # تصفير العداد لبدء الشحن
                self.state = "CHARGING"

        # 3. حالة الشحن: ننتظر الفولت يوصل 1
        elif self.state == "CHARGING":
            if self.rc_pin.value() == 1:
                t = time.ticks_diff(now, self.timer)
                self._calc_percent(t)
                self.state = "DONE" 
                
            # صمام الأمان (5 ثواني)
            elif time.ticks_diff(now, self.timer) > 5000:
                self.state = "DONE"

    def _calc_percent(self, t):
        if t <= self.TIME_FULL: self.percent = 100
        elif t >= self.TIME_EMPTY: self.percent = 0
        else:
            p = ((self.TIME_EMPTY - t) / (self.TIME_EMPTY - self.TIME_FULL)) * 100
            self.percent = max(0, min(100, int(p)))

    def start_reading(self):
        # بنستدعيها بس لما بدنا نقرأ البطارية من جديد
        if self.state == "DONE" or self.state == "IDLE":
            self.state = "IDLE"
bat = BatteryMonitor(27)
bat.update()
bat.start_reading()
per_bat = bat.percent

def check_ram():
    gc.collect() # تنظيف الذاكرة أولاً للحصول على قراءة دقيقة
    u = gc.mem_alloc()
    f = gc.mem_free()
    print("--- RAM Status ---")
    print(f"Used: {u / 1024:.2f} KB")
    print(f"Free: {f / 1024:.2f} KB")
    print(f"Usage: {(u/(u+f))*100:.1f}%")
    print("------------------")

# جرب استدعاءها قبل وبعد فتح ملف القبلة
check_ram()

# ----------------- دالة التحميل (RAM Loader) -----------------

def draw_from_ram(filename, w, h, part):
    """
    part: 1 للنصف الأول، 2 للنصف الثاني
    """
    gc.collect()
    
    # حجم الصورة كاملة بالبايت (لأن كل بكسل 2 بايت)
    total_size = w * h * 2
    # حجم النصف
    half_size = total_size // 2
    
    try:
        if filename != None:
            # نجهز بافر بحجم النصف فقط
            buffer = bytearray(half_size)
            
            with open(filename, 'rb') as f:
                if part == 1:
                    # إذا بدنا النصف الأول، نقرأ فوراً
                    f.readinto(buffer)
                elif part == 2:
                    # إذا بدنا النصف الثاني، نقفز عن النصف الأول
                    f.seek(half_size) # <--- هذا هو الأمر السحري
                    f.readinto(buffer)
            return buffer
        else:
            buffer = None
    except Exception as e:
        print("Error loading file:", e)
        return None
    
# --- دالة تشغيل الكرت مع نظام الصعقة البرمجية (Aggressive Reset) ---
def mount_sd(max_retries=5):
    global spi_sd, sd, vfs
    
    for attempt in range(max_retries):
        try:
            print(f"محاولة إنعاش الذاكرة... (المحاولة {attempt + 1} من {max_retries})")
            
            # 1. إغلاق أي اتصال سابق لتنظيف الذاكرة
            try: spi_sd.deinit()
            except: pass
            try: os.umount("/sd")
            except: pass
            
            # 2. الصعقة البرمجية (تحويل الأسلاك لـ GPIO عادي وتفريغ شحنتها)
            cs_pin = Pin(16, Pin.OUT)
            mosi_pin = Pin(3, Pin.OUT)
            sck_pin = Pin(2, Pin.OUT)
            miso_pin = Pin(4, Pin.IN, Pin.PULL_UP) # إبقاء الإدخال آمن
            
            # إجبار الكرت على تفريغ الإشارات المعلقة
            cs_pin.value(1)
            mosi_pin.value(1)
            sck_pin.value(1)
            time.sleep_ms(10)
            
            # 3. تشغيل الـ SPI بسرعة بطيئة جداً للإنعاش
            spi_sd = SPI(0, baudrate=100000, polarity=0, phase=0, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
            
            # 4. النبضات الوهمية (Dummy Clocks) والكرت مسكر (CS=1)
            cs_pin.value(1) 
            spi_sd.write(b'\xff' * 15) # إرسال 15 بايت (120 نبضة قوية)
            time.sleep_ms(10)
            
            # 5. رفع السرعة ومحاولة الاتصال الرسمية
            spi_sd.init(baudrate=5000000)
            sd = sdcard.SDCard(spi_sd, cs_pin)
            vfs = os.VfsFat(sd) # type: ignore
            os.mount(vfs, "/sd")
            
            print("✅ تم التعرف على الـ SD Card بنجاح واستيقظ من الغيبوبة!")
            return True 
            
        except Exception as e:
            print(f"⚠️ فشل في المحاولة {attempt + 1}: {e}")
            time.sleep_ms(100) # استراحة قصيرة قبل الضربة التالية
            
    print("❌ فشل تشغيل الذاكرة نهائياً.")
    return False

# --------------- الرجاج والبوصلة ---------------------
# --- دالة تهيئة الحساس (الموظف النائم) ---
def init_sensor():
    # تشغيل الوضع المستمر (Continuous) + إعادة ضبط (Reset)
    i2c.writeto_mem(ADDRESS, 0x0A, b'\xC3') 
    # إعدادات الفترة (Period) افتراضية
    i2c.writeto_mem(ADDRESS, 0x0B, b'\x00')

# --- داله البوصلة ---
def compass():
    # --- 2. قيم المعايرة (محسوبة من بياناتك السابقة) ---
    # هذه الأرقام تجعل الدائرة في المركز (0,0) بدلاً من أن تكون مشردة
    X_OFFSET = 0
    Y_OFFSET = 0
    data = i2c.readfrom_mem(ADDRESS, 0x01, 6)
    
    # تجميع البايتات (Little Endian كما اكتشفنا من الـ Dump)
    x_raw = (data[1] << 8) | data[0]
    y_raw = (data[3] << 8) | data[2]

    # تحويل القيم السالبة (Signed 16-bit)
    if x_raw > 32767: x_raw -= 65536
    if y_raw > 32767: y_raw -= 65536
    
    # === الخطوة الجوهرية: تطبيق المعايرة ===
    # نطرح قيمة المنتصف لنحصل على الصفر الحقيقي
    x_calibrated = -(x_raw - X_OFFSET)
    y_calibrated = y_raw - Y_OFFSET

    # حساب الزاوية (Heading) باستخدام atan2
    # الدالة atan2 تقوم تلقائياً بحساب الزاوية بناءً على إحداثيات الدائرة 360 درجة
    heading_rad = math.atan2(y_calibrated, x_calibrated)
    
    # تحويل من راديان إلى درجات
    heading_deg = heading_rad * (180 / math.pi)

    # زاوية الانحراف المغناطيسي (Declination Angle)
    # في الأردن (عمان) هي تقريباً +5 درجات. نضيفها لنحصل على الشمال الجغرافي
    heading_deg += 5 

    # التأكد أن الزاوية بين 0 و 360
    if heading_deg < 0:  heading_deg += 360
    if heading_deg > 360:   heading_deg -= 360

    # طباعة النتيجة النهائية
    return  heading_deg

# تشغيل الحساس
init_sensor()

# ---- رجاج
def rjrj(a):
    pass
    """global x, g, rjaj, sb7_33,sb7_33_2,no_sb7
    y=time.ticks_ms()
    if a==1: 
        if y-g >= 200:
            x=time.ticks_ms() 
        g=y   

    if y-int(x) <= 200: 
        rjaj.value(1)
    else:
        rjaj.value(0)

    if a == 2 :
        sb7_33 = time.ticks_ms()
        g=y
    elif y - sb7_33 <= 100:
        rjaj.value(1)
        no_sb7 = time.ticks_ms()
        g=y
    elif y - no_sb7 <= 50:
        rjaj.value(0)
        sb7_33_2 = time.ticks_ms()
        g=y
    elif y - sb7_33_2 <= 100:
        rjaj.value(1)
        g=y
    else:
        rjaj.value(0)"""
#-------------الصفحة البوصلة القبلة--------------------
def page_qbla():
    try: 
        global rsm_1, rsm_2, test_x, test_y, background, test_x1, test_y1, page, draw_me, job_data
        deg = compass()
        gc.collect()
        # قائمة زوايا القبلة في الأردن
        # الاسم: الزاوية    
        deg_a =  (deg - 199.6)-90
        deg_rad = math.radians(int(deg_a))
        x_b = int((-60 * math.cos(deg_rad))+120)
        x_s = 120
        y_s = 120
        y_b = int((60 * math.sin(deg_rad))+120)
        
        if 120<x_b<160 and y_b < 100:
            y_b = 78

        elif 80<x_b<=120 and y_b < 100:
            y_b = 78

        if -85>deg_a>-100:
            if rsm_1 == 0 :
                #---- الصفحة الاولى -------------
                job_data = "/sd/qbla_s7.bin"
                draw_me = draw_from_ram(job_data, 240, 240, 1)
                tft.set_window(0, 0, 240, 240)
                tft.write_data(draw_me)

                # التنظيف الفوري
                draw_me = None 
                job_data = None
                draw_from_ram(None, 0, 0, 0)
                gc.collect()

                #---- الصفحة الثانية -------------
                job_data = "/sd/qbla_s7.bin"
                draw_me = draw_from_ram(job_data, 240, 240, 2)
                tft.set_window(0, 120, 240, 240)
                tft.write_data(draw_me)

                # التنظيف الفوري
                draw_me = None 
                job_data = None
                draw_from_ram(None, 0, 0, 0)
                gc.collect()
                
                test_x = x_b
                test_y = y_b 
                test_x1 = x_s
                test_y1 = y_s 

                tft.thick_line(x_s, y_s, x_b, y_b, st7789.GREEN, thickness=5)
                
                per_bat = bat.percent
                tft.update_battery_level(2, 2, per_bat) 


            if x_b - test_x > 2 or x_b - test_x < -2:
                tft.thick_line(120, 120, test_x, test_y, swap_bytes(background), thickness=5)
                test_x = x_b
                test_y = y_b     
                tft.thick_line(x_s, y_s, x_b, y_b, st7789.GREEN, thickness=5) 
            rsm_1+=1
            rsm_2=0
        else:
            if rsm_2 == 0 : 
                #---- الصفحة الاولى -------------
                    job_data = "/sd/qbla.bin"
                    draw_me = draw_from_ram(job_data, 240, 240, 1)
                    tft.set_window(0, 0, 240, 240)
                    tft.write_data(draw_me)

                    # التنظيف الفوري
                    draw_me = None 
                    job_data = None
                    draw_from_ram(None, 0, 0, 0)
                    gc.collect()

                    #---- الصفحة الثانية -------------
                    job_data = "/sd/qbla.bin"
                    draw_me = draw_from_ram(job_data, 240, 240, 2)
                    tft.set_window(0, 120, 240, 240)
                    tft.write_data(draw_me)

                    # التنظيف الفوري
                    draw_me = None 
                    job_data = None
                    draw_from_ram(None, 0, 0, 0)
                    gc.collect()

                    per_bat = bat.percent
                    tft.update_battery_level(2, 2, per_bat)


            rsm_1 = 0
            rsm_2 +=1
            
            if x_b - test_x > 5 or x_b - test_x < -5 or  y_b - test_y < -5 or y_b - test_y > 5 :
                tft.draw_fast_line(test_x1, test_y1, test_x, test_y, background, background ,thickness=7) # red
                test_x = x_b
                test_y = y_b 
                test_x1 = x_s
                test_y1 = y_s     
                tft.draw_fast_line(x_s, y_s, x_b, y_b, swap_bytes(camel), background,thickness=7) # red
            

    except Exception as e:
        print("Error loading file:", e)
        page = 0
        tft.draw_image("menu_qbla.bin", 0, 0, 240, 240)
        pass


def sb7a(coun):
    global sf7a, page, rsm_1, rsm_2, count_sb7, ms7
    if count_sb7 > 9999998:
        tft.fill_circle(120,120,52,dark_green)
        count_sb7 = 0
        size = 3
    elif count_sb7 > 99998:
        size = 1
    elif count_sb7 > 9998:
        size = 2
    else :
        size = 3  
    if coun == -2:
        sf7a = 1 
        page = 0
        rsm_2 = 0
        rsm_1 = 0
        tft.draw_image("menu_sb7a.bin", 0, 0, 240, 240)
        with open('/sd/log_count.txt', 'w') as f:
            f.write(str(count_sb7))
    elif coun == 2:
        if ms7 == 0:
            if size == 2 :
                tft.fill_circle(120,120,55,0xF7E7)
            else:
                tft.fill_circle(120,120,55,dark_green)
        ms7 += 1
        count_sb7+=1
        x_sb7 = int(120-(int(len(str(count_sb7)))*8*size)/2)
        y_sb7 = 120-4*size
        if size == 2:
            tft.draw_number(count_sb7,x_sb7,y_sb7,dark_green,0xF7E7,size=size)
        else:
            tft.draw_number(count_sb7,x_sb7,y_sb7,0xF7E7,dark_green,size=size)
        # فتح ملف جديد (أو مسح القديم والكتابة فوقه) باستخدام 'w'
    elif coun % 3 and 90<coun<180:
        tft.fill_circle(120,120,int(coun*0.31),0x3B0A)
        x_sb7 = int(120-(int(len(str(count_sb7)))*8*size)/2)
        y_sb7 = 120-4*size
        if size == 2:
            tft.draw_number(count_sb7,x_sb7,y_sb7,dark_green,0xF7E7,size=size)
        else:
            tft.draw_number(count_sb7,x_sb7,y_sb7,0xF7E7,0x3B0A,size=size)
        ms7 = 0
    elif coun % 3 and coun>180 :
        if ms7 == 0:
            tft.fill_circle(120,120,62,dark_green)
            count_sb7 = 0
            size = 3
            x_sb7 = int(120-(int(len(str(count_sb7)))*8*size)/2)
            y_sb7 = 120-4*size
            tft.draw_number(count_sb7,x_sb7,y_sb7,0xF7E7,dark_green,size=size)
            with open('/sd/log_count.txt', 'w') as f:
                f.write(str(count_sb7))
        ms7 += 1

    if count_sb7 % 33 == 0:
        rjrj(2)

#------------------------------------------------
def menu(coun):
    global sf7a, job_data, draw_me, page, rsm_1, rsm_2, count_sb7, ms7, t3del_clock, hour_check , min_check 
    global sec_check, second_back, minute_back, hour_back, t3del_clock1, day_back, month_back, day_check 
    global mon_check, ampm, found, numS, numS1 ,per_bat_check,per_bat, bat

    if page == 0: 
        if coun == 3:
            rjrj(1)
            sf7a +=1
            if sf7a == 1 :
                tft.draw_image("menu_sb7a.bin",0,0,240,240)

            elif sf7a == 2 :
                tft.draw_image("menu_clock.bin",0,0,240,240)

            elif sf7a == 3:
                sf7a = 0
                tft.draw_image("menu_qbla.bin", 0, 0, 240, 240)
        elif coun == -3:
            rjrj(1)

            sf7a -= 1
            if sf7a == 0 :
                tft.draw_image("menu_qbla.bin", 0, 0, 240, 240)              

            elif sf7a == 1 :
                tft.draw_image("menu_sb7a.bin",0,0,240,240)

            elif sf7a == -1:
                sf7a = 2 
                tft.draw_image("menu_clock.bin",0,0,240,240)

        elif coun == 2:
            rjrj(1)

            if sf7a == 0:
                tft.draw_image("/sd/qbla.bin",0,0,240,240)
                page = 1
            
            elif sf7a == 1: #--------الصفحة الاولى من المسبحة -----------------
                ms7 += 1
                tft.draw_image("/sd/sb7a.bin",0,0,240,240)
                if count_sb7 > 9999998:
                    tft.fill_circle(120,120,52,dark_green)
                    count_sb7 = 0
                    size = 3
                elif count_sb7 > 99998:
                    tft.fill_circle(120,120,52,dark_green)
                    size = 1
                elif count_sb7 > 9998:
                    tft.fill_circle(120,120,50,0xF7E7)
                    size = 2
                else :
                    size = 3 
                x_sb7 = int(120-(int(len(str(count_sb7)))*8*size)/2)
                y_sb7 = 120-4*size
                if size == 2:
                    tft.draw_number(count_sb7,x_sb7,y_sb7,dark_green,0xF7E7,size=size)
                else:
                    tft.draw_number(count_sb7,x_sb7,y_sb7,0xF7E7,dark_green,size=size)
                page = 2

            elif sf7a == 2: #-------- الساعة ------------
                tft.draw_image("/sd/clock.bin", 0, 0, 240, 240)
                t3del_clock = 0
                hour_check = 0
                min_check = 0
                sec_check = 0
                day_check = 0
                page = 3


    elif page == 1:
        if coun == -2:
            rjrj(1)

            sf7a = 0 
            page = 0
            rsm_2 = 0
            rsm_1 = 0
            tft.draw_image("menu_qbla.bin", 0, 0, 240, 240)
   
    elif page == 2: #--------داخل صفحة السبحة-----------
        try: 
            sb7a(coun)
        except Exception as e :
            print(e)
            page = 0 
            tft.draw_image("menu_sb7a.bin",0,0,240,240)
            return 0
        
    elif page == 3:
        try: 
            rjrj(1)
            if coun == 2 :
                t3del_clock +=1
                t3del_clock1 = 0
                if t3del_clock == 6 :
                    t3del_clock = 0
                    if ampm == "AM" and int(hour_check) > 11 : hour_check = int(hour_check)-12
                    elif ampm =="PM" and int(hour_check) < 12 : hour_check = int(hour_check)+12
                    
                    numS,found = row(day_check,mon_check,hour_check,min_check)

                    rtc.datetime((2026, int(mon_check), int(day_check), 0, int(hour_check), int(min_check), int(sec_check), 0))
                    with open('log_clock.txt', 'w') as f:
                        f.write(f"{hour_check}:{min_check}:{sec_check}:{day_check}:{mon_check}")
                    hour_check = 0
                    min_check = 0
                    sec_check = 0
                    day_check = 0

                    #---- الصفحة الاولى -------------
                    job_data = "/sd/clock.bin"
                    draw_me = draw_from_ram(job_data, 240, 240, 1)
                    tft.set_window(0, 0, 240, 240)
                    tft.write_data(draw_me)

                    # التنظيف الفوري
                    draw_me = None 
                    job_data = None
                    draw_from_ram(None, 0, 0, 0)

                    #---- الصفحة الثانية -------------
                    job_data = "/sd/clock.bin"
                    draw_me = draw_from_ram(job_data, 240, 240, 2)
                    tft.set_window(0, 120, 240, 240)
                    tft.write_data(draw_me)

                    # التنظيف الفوري
                    draw_me = None 
                    job_data = None
                    draw_from_ram(None, 0, 0, 0)
            elif coun == -2:
                t3del_clock -=1
                t3del_clock1 = 0
                if t3del_clock == -1:
                    page = 0 
                    tft.draw_image("menu_clock.bin",0,0,240,240)
                    with open('log_clock.txt', 'w') as f:
                        f.write(f"{hour_back}:{minute_back}:{second_back}:{day_back}:{month_back}")
                elif t3del_clock == 0 :
                    if ampm == "AM" and int(hour_check) > 12 : hour_check = int(hour_check)-12
                    elif ampm =="PM" and int(hour_check) < 12 : hour_check = int(hour_check)+12
                    
                    numS,found = row(day_check,mon_check,hour_check,min_check)
                    
                    rtc.datetime((2026, int(mon_check), int(day_check), 0, int(hour_check), int(min_check), int(sec_check), 0))
                    with open('log_clock.txt', 'w') as f:
                        f.write(f"{hour_check}:{min_check}:{sec_check}:{day_check}:{mon_check}")
                    hour_check = 0
                    min_check = 0
                    sec_check = 0
                    day_check = 0
                    #---- الصفحة الاولى -------------
                    job_data = "/sd/clock.bin"
                    draw_me = draw_from_ram(job_data, 240, 240, 1)
                    tft.set_window(0, 0, 240, 240)
                    tft.write_data(draw_me)

                    # التنظيف الفوري
                    draw_me = None 
                    job_data = None
                    draw_from_ram(None, 0, 0, 0)

                    #---- الصفحة الثانية -------------
                    job_data = "/sd/clock.bin"
                    draw_me = draw_from_ram(job_data, 240, 240, 2)
                    tft.set_window(0, 120, 240, 240)
                    tft.write_data(draw_me)

                    # التنظيف الفوري
                    draw_me = None 
                    job_data = None
                    draw_from_ram(None, 0, 0, 0)

            if t3del_clock == 1:
                t3del_clock1 +=1 
                if t3del_clock1 == 1:
                    tft.fill_triangle(41,65,24,91,58,91,st7789.GREEN)
                    tft.fill_triangle(41,156,24,131,58,131,st7789.GREEN)

                    tft.fill_triangle(120,65,103,91,137,91,st7789.RED)
                    tft.fill_triangle(120,156,103,131,137,131,st7789.RED)

                    tft.fill_triangle(204,65,187,91,221,91,st7789.RED)
                    tft.fill_triangle(204,156,187,131,221,131,st7789.RED)
                   
                if coun == -3:
                    hour_check = int(hour_check)+1
                    if hour_check == 24:
                        hour_check = 0
                    clock(1)
                elif coun == 3 :   
                    hour_check = int(hour_check)-1
                    if hour_check == -1 :
                        hour_check = 23
                    clock(1)
                elif coun < -120 and coun % 2:
                    hour_check = int(hour_check)+1
                    if hour_check == 24:
                        hour_check = 0
                    clock(1)
                elif coun > 120 and coun % 2:
                    hour_check = int(hour_check)-1
                    if hour_check == -1 :
                        hour_check = 23
                    clock(1)   

            elif t3del_clock == 2:
                t3del_clock1 +=1 
                if t3del_clock1 == 1:
                    tft.fill_triangle(41,65,24,91,58,91,st7789.RED)
                    tft.fill_triangle(41,156,24,131,58,131,st7789.RED)

                    tft.fill_triangle(120,65,103,91,137,91,st7789.GREEN)
                    tft.fill_triangle(120,156,103,131,137,131,st7789.GREEN)

                    tft.fill_triangle(204,65,187,91,221,91,st7789.RED)
                    tft.fill_triangle(204,156,187,131,221,131,st7789.RED)
                if coun == -3:
                    min_check = int(min_check)+1
                    if min_check == 60:
                        min_check = 0    
                    clock(2)
                elif coun == 3 :
                    min_check = int(min_check)-1
                    if min_check == -1 :
                        min_check = 59
                    clock(2)
                elif coun < -120 and coun % 2:
                    min_check = int(min_check)+1
                    if min_check == 60:
                        min_check = 0    
                    clock(2)
                elif coun > 120 and coun % 2 :
                    min_check = int(min_check)-1
                    if min_check == -1 :
                        min_check = 59
                    clock(2)     

            elif t3del_clock == 3:
                t3del_clock1 +=1 
                if t3del_clock1 == 1:
                    tft.draw_number(ampm,212,68,st7789.WHITE,0xFB6D,size=1)

                    tft.fill_triangle(120,65,103,91,137,91,st7789.RED)
                    tft.fill_triangle(120,156,103,131,137,131,st7789.RED)

                    tft.fill_triangle(204,65,187,91,221,91,st7789.GREEN)
                    tft.fill_triangle(204,156,187,131,221,131,st7789.GREEN)
                if coun == -3:
                    sec_check = int(sec_check)+1
                    if sec_check == 60:
                        sec_check = 0
                    clock(3)
                elif coun == 3 :
                    sec_check = int(sec_check)-1
                    if sec_check == -1:
                        sec_check = 59
                    clock(3)
                elif coun < -120 and coun % 2:
                    sec_check = int(sec_check)+1
                    if sec_check == 60:
                        sec_check = 0
                    clock(3)    
                elif coun > 120 and coun % 2:
                    sec_check = int(sec_check)-1
                    if sec_check == -1:
                        sec_check = 59
                    clock(3)

            elif t3del_clock == 5:
                t3del_clock1 +=1 
                if t3del_clock1 == 1:
                    tft.draw_number(ampm,212,68,st7789.WHITE,0xFB6D,size=1)

                    tft.fill_triangle(120,65,103,91,137,91,st7789.RED)
                    tft.fill_triangle(120,156,103,131,137,131,st7789.RED)

                    tft.fill_triangle(204,65,187,91,221,91,st7789.RED)
                    tft.fill_triangle(204,156,187,131,221,131,st7789.RED)

                    tft.thick_line(126,179,232,179,st7789.GREEN,5)
                if coun == -3:
                    day_check = int(day_check)+1

                    if mon_check == 12 and day_check == 32:
                        mon_check = 1
                        day_check = 1
                    elif (mon_check == (1 or 3 or 5 or 7 or 8 or 10)) and day_check == 32:
                        mon_check +=1
                        day_check = 1
                    elif mon_check == 2 and day_check == 30: 
                        mon_check +=1
                        day_check = 1   
                    elif day_check==31 :
                        mon_check+=1 
                        day_check = 1

                    clock(4)
                elif coun == 3 :
                    day_check = int(day_check)-1
                    if day_check == 0:
                        mon_check -= 1
                        if mon_check == 0:
                            mon_check = 12
                            day_check = 31    
                        elif (mon_check == (1 or 3 or 5 or 7 or 8 or 10)):
                            day_check = 31
                        elif mon_check == 2 : 
                            day_check = 29 
                        else: 
                            day_check = 30
                    clock(4)    
                elif coun > 120 and coun % 2:
                    day_check = int(day_check)-1
                    if day_check == 0:
                        mon_check -= 1
                        if mon_check == 0:
                            mon_check = 12
                            day_check = 31    
                        elif (mon_check == (1 or 3 or 5 or 7 or 8 or 10)):
                            day_check = 31
                        elif mon_check == 2 : 
                            day_check = 29 
                        else: 
                            day_check = 30
                    clock(4) 
                elif coun <-120 and coun % 2 == 0:
                    day_check = int(day_check)+1

                    if mon_check == 12 and day_check == 32:
                        mon_check = 1
                        day_check = 1
                    elif (mon_check == (1 or 3 or 5 or 7 or 8 or 10)) and day_check == 32:
                        mon_check +=1
                        day_check = 1
                    elif mon_check == 2 and day_check == 30: 
                        mon_check +=1
                        day_check = 1   
                    elif day_check==31 :
                        mon_check+=1 
                        day_check = 1

                    clock(4)

            elif t3del_clock == 4:
                t3del_clock1 +=1 
                if t3del_clock1 == 1:
                    tft.draw_number(ampm,212,68,st7789.GREEN,0xFB6D,size=1)

                    tft.fill_triangle(120,65,103,91,137,91,st7789.RED)
                    tft.fill_triangle(120,156,103,131,137,131,st7789.RED)

                    tft.fill_triangle(204,65,187,91,221,91,st7789.RED)
                    tft.fill_triangle(204,156,187,131,221,131,st7789.RED)
                    

                    tft.thick_line(126,179,232,179,st7789.WHITE,5)
                if coun == -3 or coun == 3:
                    if ampm =="AM": ampm="PM"
                    else : ampm = "AM"
                    tft.draw_number(ampm,212,68,st7789.GREEN,0xFB6D,size=1)                
        
        except Exception as e :
            print(e)
            page = 0 
            tft.draw_image("menu_clock.bin",0,0,240,240)
            return 0
    
    if coun == 2 or coun == -2 or coun ==3 or coun ==-3:
        per_bat = bat.percent
        tft.update_battery_level(2, 2, per_bat)
    

def clock(n=0):
    global second_back, minute_back, hour_back, hour_check, min_check, sec_check, day_back, month_back, day_check 
    global mon_check, ampm, hour_12, found, numS, numS1
    x_hour = int(17)
    x_min = int(96)
    x_second = int(175)
    y_time = const(100)

  
    if n == 0:
        if hour_back > 11:
            ampm = "PM"
            ampmcolor = st7789.BLACK
        else:
            ampm = "AM"
            ampmcolor = st7789.WHITE
        
        if second_back < 10 :
            if sec_check != f"0{second_back}":
                sec_check = f"0{second_back}"
                tft.draw_number(sec_check,x_second,y_time,0x0204,0xEF5A,size=3)
            
        elif sec_check != str(second_back):
            tft.draw_number(second_back,x_second,y_time,0x0204,0xEF5A,size=3)
            sec_check = str(second_back)
        
        if minute_back < 10 :
            if min_check != f"0{minute_back}":
                min_check = f"0{minute_back}"
                tft.draw_number(min_check,x_min,y_time,0x0204,0xEF5A,size=3)
                
                numS,found = row(day_back,month_back,hour_back,minute_back)

        elif min_check != str(minute_back) :
            tft.draw_number(minute_back,x_min,y_time,0x0204,0xEF5A,size=3)  
            min_check = str(minute_back)
            numS,found = row(day_back,month_back,hour_back,minute_back)

        if hour_back < 10:
            if hour_check != f"0{int(hour_back)}":
                hour_check = f"0{int(hour_back)}" 
                if int(hour_back) == 0:
                    hour_12 = 12
                else:
                    hour_12 = f"0{int(hour_back)}" 
                tft.draw_number(hour_12,x_hour,y_time,0x0204,0xEF5A,size=3)
                
                tft.draw_number(ampm,212,68,ampmcolor,0xFB6D,size=1)

        elif hour_check != str(hour_back) :
            if int(hour_back) >= 22: hour_12 = int(hour_back) - 12
            elif 22 > int(hour_back) > 12: hour_12 = f"0{int(hour_back) - 12}"
            else: hour_12 = int(hour_back)    
            tft.draw_number(hour_12,x_hour,y_time,0x0204,0xEF5A,size=3)
            hour_check = str(hour_back)

            tft.draw_number(ampm,212,68,ampmcolor,0xFB6D,size=1)


        if day_check != day_back:
            #كتابة اليوم
            if day_back < 10:
                day_back_f = f"0{day_back}"
            else :
                day_back_f = day_back
            if month_back < 10 :
                month_back_f =f"0{month_back}"
            else :
                month_back_f = month_back

            tft.draw_number(f"{day_back_f}-{month_back_f}",129,161,0x0204,0xE3EF,size=1)

            #مواقيت الصلاة كل يوم بتغيرو
            slah_color(numS,found,"color")
            tft.draw_number(found[0],196,222,f_color,0xEEB7,size=1) # type: ignore
            tft.draw_number(found[2],149,222,d_color,0xEEB7,size=1) # type: ignore
            tft.draw_number(found[3],103,222,asr_color,0xEEB7,size=1)# type: ignore
            tft.draw_number(found[4],56,222,m_color,0xEEB7,size=1)# type: ignore
            tft.draw_number(found[5],7,222,ash_color,0xEEB7,size=1)# type: ignore
            
            day_check = day_back
            mon_check = month_back

        if numS1 != numS:
            numS1 = numS
            slah_color(numS,found,"txt")

    elif n == 1:
        if hour_check == 0: hour_12 = 12
        elif hour_check < 10: hour_12 = f"0{hour_check}"
        elif 12>= hour_check >=10 : hour_12 = hour_check
        elif 22> hour_check > 12 : hour_12 = f"0{hour_check-12}"
        elif hour_check >= 22 : hour_12 = hour_check-12
        tft.draw_number(hour_12,x_hour,y_time,0x0204,0xEF5A,size=3)
    elif n == 2:
        if int(min_check) < 10 :
            min_check = f"0{min_check}"
            tft.draw_number(min_check,x_min,y_time,0x0204,0xEF5A,size=3)
        else:    
            tft.draw_number(int(min_check),x_min,y_time,0x0204,0xEF5A,size=3)   
    elif n == 3:
        if int(sec_check) < 10 :
            sec_check = f"0{sec_check}"
            tft.draw_number(sec_check,x_second,y_time,0x0204,0xEF5A,size=3)
        else:    
            tft.draw_number(int(sec_check),x_second,y_time,0x0204,0xEF5A,size=3) 
    elif n == 4 :
        if day_check < 10:
                day_back_f = f"0{day_check}"
        else :
            day_back_f = day_check
        if mon_check < 10 :
            month_back_f =f"0{mon_check}"
        else :
            month_back_f = mon_check

        tft.draw_number(f"{day_back_f}-{month_back_f}",129,161,0x0204,0xE3EF,size=1)        
    

#------------------ القبلة-ر   --------------
qibla_locations = [
    ["Ruwaished (East)", 162.5],
    ["Safawi/Azraq", 160.5],
    ["Irbid/Mafraq", 159.5],
    ["Amman/Zarqa", 158.5],
    ["Dead Sea/Madaba", 157.5],
    ["Karak/Tafilah", 156.5],
    ["Maan/Petra", 155.5],
    ["Aqaba (South)", 154.5]
]


# ----------------- النواة الثانية (Core 1) -----------------
def core1_task():
    global job_data, draw_me, width, height, count, page, sf7a, sys_on, t3del_clock, sys_off, per_bat
    
    page = 0
    sf7a = 0
    tft.draw_image("menu_qbla.bin", 0, 0, 240, 240)
    check_ram()

    tft.update_battery_level(2, 2, per_bat)
    per_bat_check = per_bat
    per_bat_time = time.ticks_ms()
    while True:
        time.sleep(1)
        while sys_on == 1:
            time.sleep_ms(10) # تأخير بسيط جداً للأمان
            
            rjrj(0)

            if job_data is not None:
                # هنا يحدث التحميل الثقيل
                draw_me = draw_from_ram(job_data, width, height, 1)
                #draw_me = draw_from_ram(job_data,widht,height,part)
                # تم التنفيذ، نصفر الطلب
                job_data = None
                # تشغيل المكنسة في الخلفية أيضاً
                gc.collect()

            #rjrj(b)
            #b += 1
            #b = 0

            if count != 0:
                menu(count)
            
            elif page == 1:
                page_qbla()

            elif page == 3:
                try:
                    if t3del_clock == 0:
                        clock()

                except Exception as e:
                    print(e)
                    page = 0
                    tft.draw_image("menu_clock.bin",0,0,240,240)
            
            if time.ticks_diff(time.ticks_ms(), per_bat_time) > 300000:#كل خمس دقائق يشوف كم صارت البطارية
                per_bat = bat.percent
                print(per_bat)
                per_bat_time = time.ticks_ms()

            if per_bat_check != per_bat:
                tft.update_battery_level(2, 2, per_bat)
                per_bat_check = per_bat
   
        if sys_off == 0 and core1==1:     
            tft.sleep_mode(True)
            time.sleep_ms(20)
            screen.value(0)
            print("done, now core1_ is off")
            sys_off = -3 

last_check_time = time.ticks_ms()
file_check_time = time.ticks_ms()

# ----------------- النواة الرئيسية (Core 0) -----------------
while True:
    # 1. قراءة الوقت الفعلي من الـ RTC براحة تامة
    t = rtc.datetime()
    # t = (year, month, day, weekday, hour, minute, second, subsecond)
    month_back = t[1]
    day_back = t[2]
    hour_back = t[4]
    minute_back = t[5]
    second_back = t[6]


    if on_sys.value():
        if sys_on == 0:
            #تشغيل الشاشة
            time.sleep_ms(100)
            screen.value(1)
            time.sleep_ms(100)
            tft.sleep_mode(False)
            tft.draw_image("loading.bin",0,0,240,240)
            time.sleep_ms(400)

            if sd_on == 0:
                # تفريغ أي حالة Mount معلقة من قبل بالسوفتوير
                try: os.umount("/sd")
                except: pass
                # --- الإضافة الجديدة: إيقاظ الـ SD Card والـ SPI ---
                try:
                    # لازم ترجع تعمل Init للـ SPI (ونصيحة نزل السرعة لـ 5 ميجا عشان ما يضرب)
                    spi_sd = SPI(0, baudrate=5000000, polarity=0, phase=0, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
                    cs = Pin(16, Pin.OUT)
                    sd = sdcard.SDCard(spi_sd, cs)
                    vfs = os.VfsFat(sd) # type: ignore
                    os.mount(vfs, "/sd")
                except Exception as e:
                    print("Error waking up SD:", e)
                    mount_sd(10)
                # -------------------------------------------------
                sd_on = 1
            tft.draw_image("menu_qbla.bin",0,0,240,240)
            page = 0
            sf7a = 0
            time.sleep_ms(100)
            sys_on = 1
            # تشغيل النواة الثانية
            time.sleep_ms(10)
            if core1 == 0 :
                core1=1
                _thread.start_new_thread(core1_task, ())
            
        sys_off = 0

        # 1. تحديث حالة البطارية (هاد السطر بياخذ أجزاء من المايكرو ثانية وما بيجمد الكود)
        bat.update()
        
        # 2. كل 5 دقايق بنعطيه أمر يرجع يقرأ البطارية
        if time.ticks_diff(time.ticks_ms(), last_check_time) > 300000:#كل خمس دقائق يشوف كم صارت البطارية
            check_ram()
            bat.start_reading()
            last_check_time = time.ticks_ms()
            print("ok?")

        if but_Down.value()==1:
            count+=3
            time.sleep_ms(15) # تأخير بسيط جداً للأمان

        elif but_Up.value()==1:
            count-=3
            time.sleep_ms(15) # تأخير بسيط جداً للأمان

        elif but_R.value()==1:
            count += 2
            time.sleep_ms(15) # تأخير بسيط جداً للأمان

        elif but_L.value()==1:
            count -= 2
            time.sleep_ms(15) # تأخير بسيط جداً للأمان

        else:
            count = 0  
   
    elif on_sys.value()!=1 :
        sys_on = 0
        if sys_off < 0:
            time.sleep_ms(50)
            # التنظيف الفوري
            draw_me = None 
            job_data = None
            time.sleep_ms(250)
            # --- الإضافة الجديدة: فك الـ SD Card وإطفاء الـ SPI قبل النوم ---
            # 1. إغلاق أي اتصال سابق لتنظيف الذاكرة
            try: spi_sd.deinit()
            except: pass
            try: os.umount("/sd")
            except: pass
            
            # 2. الصعقة البرمجية (تحويل الأسلاك لـ GPIO عادي وتفريغ شحنتها)
            cs_pin = Pin(16, Pin.OUT)
            mosi_pin = Pin(3, Pin.OUT)
            sck_pin = Pin(2, Pin.OUT)
            miso_pin = Pin(4, Pin.IN, Pin.PULL_UP) # إبقاء الإدخال آمن
            
            # إجبار الكرت على تفريغ الإشارات المعلقة
            cs_pin.value(1)
            mosi_pin.value(1)
            sck_pin.value(1)
            time.sleep_ms(10)
            # -----------------------------------------------------------
            sd_on = 0
            sys_off = 10
            time.sleep_ms(100)
            gc.collect()

        elif sys_off > 5:
            time.sleep_ms(100)
            lightsleep(1000)
            if time.ticks_diff(time.ticks_ms(), file_check_time) > 2700000:#كل 45 دقيقة يحفظ الساعة
                file_check_time = time.ticks_ms()
                print("saving time...")
                with open('log_clock.txt', 'w') as f:
                    f.write(f"{hour_back}:{minute_back}:{second_back}:{day_back}:{month_back}")



    # تفقد هل وصلت الصورة من النواة الثانية؟

    """
    job_data = "/sd/img.bin"
    if draw_me != None and page !=0:
        # الرسم السريع
        tft.set_window(0, 0, 240 - 1, 240 - 1)
        tft.write_data(draw_me)

        # التنظيف الفوري
        draw_me = None
        job_data = None
        draw_from_ram(None,0,0)"""

   