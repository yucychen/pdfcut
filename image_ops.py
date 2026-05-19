"""
图像处理工具:
  - 自动裁白边 (auto_crop_whitespace)
  - 智能方向识别  (auto_orient_invoice)
"""
import numpy as np
from PIL import Image, ImageOps

# ---------- 1. 自动裁白边 ----------

def auto_crop_whitespace(img: Image.Image,
                         threshold: int = 240,
                         padding: int = 8) -> Image.Image:
    """
    去掉扫描件四周的白边
    threshold: 像素亮度 >= 此值视为"白" (0-255)
    padding:   裁剪后保留的内边距(px)
    """
    if img.mode != "RGB":
        img = img.convert("RGB")

    gray = img.convert("L")
    arr = np.array(gray)
    mask = arr < threshold  # 非白像素
    if not mask.any():
        return img  # 全白, 不裁

    ys, xs = np.where(mask)
    top, bottom = ys.min(), ys.max()
    left, right = xs.min(), xs.max()

    top    = max(0, top - padding)
    left   = max(0, left - padding)
    bottom = min(img.height - 1, bottom + padding)
    right  = min(img.width  - 1, right  + padding)

    if right <= left or bottom <= top:
        return img
    return img.crop((left, top, right + 1, bottom + 1))


# ---------- 2. 智能方向识别 ----------

def _orient_by_tesseract(img: Image.Image):
    """用 Tesseract OSD 检测旋转角度, 返回 0/90/180/270, 失败返回 None"""
    try:
        import pytesseract
        small = img.copy()
        small.thumbnail((1200, 1200))
        osd = pytesseract.image_to_osd(small)
        for line in osd.splitlines():
            if line.lower().startswith("rotate:"):
                return int(line.split(":")[1].strip()) % 360
    except Exception:
        return None
    return None


def _orient_by_aspect(img: Image.Image, target_landscape: bool = True) -> int:
    is_landscape = img.width >= img.height
    if target_landscape and not is_landscape:
        return 90
    if (not target_landscape) and is_landscape:
        return 90
    return 0


def auto_orient_invoice(img: Image.Image,
                        prefer_landscape: bool = True,
                        use_ocr: bool = True) -> Image.Image:
    """
    自动把发票转到正确朝向
    1) 优先用 Tesseract OSD 识别旋转角
    2) 失败/未安装时按宽高比转横向 (发票通常是横版)
    """
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    angle = None
    if use_ocr:
        angle = _orient_by_tesseract(img)

    if angle is None:
        angle = _orient_by_aspect(img, target_landscape=prefer_landscape)

    if angle % 360 != 0:
        img = img.rotate(-angle, expand=True, fillcolor=(255, 255, 255))
    return img
