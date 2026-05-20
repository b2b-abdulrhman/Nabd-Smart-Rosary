import sys
import struct
from PIL import Image

# --- إعدادات ---
# اسم الصورة اللي بدك تحولها (غير الاسم هون)
INPUT_IMAGE = input("the input image: ")
# اسم الملف اللي رح يطلع (هذا اللي بتنسخه للمتحكم)
OUTPUT_FILE = input("the image name out: ")


def color_to_rgb565(r, g, b):
    """تحويل لون واحد من RGB888 إلى RGB565"""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def convert_image():
    try:
        img = Image.open(INPUT_IMAGE)
    except FileNotFoundError:
        print(f"خطأ: الملف {INPUT_IMAGE} مش موجود!")
        return

    # التأكد أن الصورة بنظام RGB
    img = img.convert("RGB")
    width, height = img.size
    print(f"جاري تحويل الصورة: {width}x{height} بكسل...")

    with open(OUTPUT_FILE, "wb") as f:
        # المرور على كل بكسل
        for y in range(height):
            for x in range(width):
                r, g, b = img.getpixel((x, y))

                # تحويل اللون إلى 16-bit RGB565
                # ملاحظة: الكود عندك بيستخدم Big Endian (>)
                rgb565 = color_to_rgb565(r, g, b)

                # كتابة البايتات (High Byte ثم Low Byte)
                f.write(struct.pack(">H", rgb565))

    print(f"تم التحويل بنجاح! الملف الجاهز: {OUTPUT_FILE}")
    print(f"الحجم: {width}x{height}")
    print("الآن انسخ ملف .bin إلى المتحكم واستخدم الأمر:")
    print(f"tft.draw_image('{OUTPUT_FILE}', x, y, {width}, {height})")


if __name__ == "__main__":
    convert_image()