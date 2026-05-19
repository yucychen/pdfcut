"""
公共工具：图片 / PDF 合并
功能:
  - 图片自适应 A4
  - 发票模式: 多张发票按 2x3 拼到 A4
  - 智能方向识别 / 自动裁白边 / 自动编号
"""
import io
import os
from PIL import Image, ImageOps, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from image_ops import auto_crop_whitespace, auto_orient_invoice

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
PDF_EXTS = {".pdf"}
SUPPORTED_EXTS = IMAGE_EXTS | PDF_EXTS

DPI = 150
PAGE_SIZES_MM = {
    "A4":       (210, 297),
    "A4_LAND":  (297, 210),
    "A5":       (148, 210),
    "LETTER":   (216, 279),
    "AUTO":     None,
}
MARGIN_MM = 5


def mm_to_px(mm, dpi=DPI):  return int(round(mm / 25.4 * dpi))
def is_supported(p):        return os.path.splitext(p)[1].lower() in SUPPORTED_EXTS
def is_image(p):            return os.path.splitext(p)[1].lower() in IMAGE_EXTS


def get_page_size_px(page):
    size = PAGE_SIZES_MM.get(page.upper())
    if size is None: return None
    w, h = size
    return mm_to_px(w), mm_to_px(h)


def _flatten_to_rgb(img):
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        return bg
    if img.mode == "P":
        return _flatten_to_rgb(img.convert("RGBA"))
    return img if img.mode == "RGB" else img.convert("RGB")


def _open_image(path):
    img = Image.open(path)
    try: img = ImageOps.exif_transpose(img)
    except Exception: pass
    return _flatten_to_rgb(img)


def fit_image_to_box(img, box_w, box_h):
    iw, ih = img.size
    s = min(box_w / iw, box_h / ih)
    return img.resize((max(1, int(iw * s)), max(1, int(ih * s))), Image.LANCZOS)


# ---------- 编号 ----------
def _load_font(size: int):
    for name in ("arial.ttf", "Arial.ttf", "DejaVuSans-Bold.ttf",
                 "/System/Library/Fonts/Supplemental/Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_number_badge(canvas: Image.Image, x: int, y: int, w: int, h: int,
                      number: int):
    """在格子右下角画编号徽标"""
    draw = ImageDraw.Draw(canvas)
    text = f"#{number}"
    font_size = max(14, h // 18)
    font = _load_font(font_size)

    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        tw, th = font.getsize(text) if hasattr(font, "getsize") else (40, 16)

    pad = max(4, font_size // 3)
    box_w, box_h = tw + pad * 2, th + pad * 2
    bx1 = x + w - box_w - 4
    by1 = y + h - box_h - 4
    bx2, by2 = bx1 + box_w, by1 + box_h

    draw.rectangle([bx1, by1, bx2, by2], fill=(255, 220, 0), outline=(120, 90, 0))
    draw.text((bx1 + pad, by1 + pad - 2), text, fill=(0, 0, 0), font=font)


# ---------- 普通图片转 PDF (自适应 A4) ----------
def fit_image_to_page(img, page_size_px, margin_px):
    pw, ph = page_size_px
    resized = fit_image_to_box(img, pw - margin_px * 2, ph - margin_px * 2)
    canvas = Image.new("RGB", (pw, ph), (255, 255, 255))
    canvas.paste(resized, ((pw - resized.width) // 2, (ph - resized.height) // 2))
    return canvas


def image_to_pdf_reader(image_path, page="A4", margin_mm=MARGIN_MM,
                        auto_orient=True):
    img = _open_image(image_path)
    page_size_px = get_page_size_px(page)
    if page_size_px is None:
        out = img
    else:
        if auto_orient and page.upper() in {"A4", "A5", "LETTER"}:
            if img.width > img.height:
                if page.upper() == "A4":
                    page_size_px = get_page_size_px("A4_LAND")
                else:
                    w, h = page_size_px; page_size_px = (h, w)
        out = fit_image_to_page(img, page_size_px, mm_to_px(margin_mm))

    buf = io.BytesIO()
    out.save(buf, format="PDF", resolution=float(DPI))
    buf.seek(0)
    return PdfReader(buf)


# ---------- 发票模式 ----------
def _invoice_layout(per_page):
    m = {1: (1, 1), 2: (1, 2), 3: (1, 3),
         4: (2, 2), 5: (2, 3), 6: (2, 3)}
    return m[max(1, min(6, per_page))]


def _prepare_invoice_image(path, smart_orient=True, use_ocr=True,
                           auto_crop=True, crop_threshold=240, crop_padding=8):
    img = _open_image(path)
    if smart_orient:
        try:
            img = auto_orient_invoice(img, prefer_landscape=True, use_ocr=use_ocr)
        except Exception as e:
            print(f"⚠️ 方向识别失败({path}): {e}")
    if auto_crop:
        try:
            img = auto_crop_whitespace(img, threshold=crop_threshold,
                                       padding=crop_padding)
        except Exception as e:
            print(f"⚠️ 裁白边失败({path}): {e}")
    return img


def build_invoice_pages(image_paths, per_page=6, page="A4",
                        margin_mm=MARGIN_MM, gap_mm=3, draw_border=True,
                        smart_orient=True, use_ocr=True,
                        auto_crop=True, crop_threshold=240, crop_padding=8,
                        number_invoices=True, start_number=1):
    page_size_px = get_page_size_px(page) or get_page_size_px("A4")
    pw, ph = page_size_px
    mp = mm_to_px(margin_mm); gp = mm_to_px(gap_mm)

    cols, rows = _invoice_layout(per_page)
    cell_w = (pw - mp * 2 - gp * (cols - 1)) // cols
    cell_h = (ph - mp * 2 - gp * (rows - 1)) // rows

    pages = []
    counter = start_number
    for i in range(0, len(image_paths), per_page):
        batch = image_paths[i:i + per_page]
        canvas = Image.new("RGB", (pw, ph), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        for idx, p in enumerate(batch):
            r, c = divmod(idx, cols)
            x0 = mp + c * (cell_w + gp)
            y0 = mp + r * (cell_h + gp)

            try:
                img = _prepare_invoice_image(
                    p, smart_orient=smart_orient, use_ocr=use_ocr,
                    auto_crop=auto_crop, crop_threshold=crop_threshold,
                    crop_padding=crop_padding,
                )
                if (cell_w > cell_h and img.width < img.height) or \
                   (cell_w < cell_h and img.width > img.height):
                    img = img.rotate(90, expand=True, fillcolor=(255, 255, 255))

                resized = fit_image_to_box(img, cell_w, cell_h)
                ox = x0 + (cell_w - resized.width) // 2
                oy = y0 + (cell_h - resized.height) // 2
                canvas.paste(resized, (ox, oy))

                if draw_border:
                    draw.rectangle([x0, y0, x0 + cell_w, y0 + cell_h],
                                   outline=(200, 200, 200), width=1)
                if number_invoices:
                    draw_number_badge(canvas, x0, y0, cell_w, cell_h, counter)
                counter += 1
            except Exception as e:
                print(f"❌ 处理失败: {p} -> {e}")
                counter += 1

        pages.append(canvas)
    return pages, counter


# ---------- 合并入口 ----------
def merge_files(input_files, output_file,
                page="A4", margin_mm=MARGIN_MM, auto_orient=True,
                invoice_mode=False, invoices_per_page=6,
                invoice_gap_mm=3, invoice_border=True,
                smart_orient=True, use_ocr=True,
                auto_crop=True, crop_threshold=240, crop_padding=8,
                number_invoices=True,
                log=print):
    writer = PdfWriter()
    total_pages = 0; used = 0

    items = []
    for path in input_files:
        if not os.path.isfile(path):
            log(f"⚠️  跳过(不存在): {path}"); continue
        if not is_supported(path):
            log(f"⚠️  跳过(不支持): {path}"); continue
        items.append(("img" if is_image(path) else "pdf", path))

    if not items:
        log("没有可合并的文件"); return False

    if not invoice_mode:
        for kind, path in items:
            try:
                reader = (image_to_pdf_reader(path, page=page,
                                              margin_mm=margin_mm,
                                              auto_orient=auto_orient)
                          if kind == "img" else PdfReader(path))
                for p in reader.pages: writer.add_page(p)
                total_pages += len(reader.pages); used += 1
                log(f"✅ 已添加: {os.path.basename(path)} ({len(reader.pages)} 页)")
            except Exception as e:
                log(f"❌ 失败: {path} -> {e}")
    else:
        log(f"📑 发票模式: {invoices_per_page} 张/页 | "
            f"智能转向={'OCR' if (smart_orient and use_ocr) else ('启发式' if smart_orient else '关')} "
            f"| 裁白边={'开' if auto_crop else '关'} "
            f"| 编号={'开' if number_invoices else '关'}")

        img_buffer = []
        counter = [1]

        def flush():
            nonlocal total_pages, used
            if not img_buffer: return
            try:
                pages, next_no = build_invoice_pages(
                    img_buffer,
                    per_page=invoices_per_page,
                    page=page, margin_mm=margin_mm,
                    gap_mm=invoice_gap_mm, draw_border=invoice_border,
                    smart_orient=smart_orient, use_ocr=use_ocr,
                    auto_crop=auto_crop, crop_threshold=crop_threshold,
                    crop_padding=crop_padding,
                    number_invoices=number_invoices,
                    start_number=counter[0],
                )
                buf = io.BytesIO()
                pages[0].save(buf, format="PDF", resolution=float(DPI),
                              save_all=True, append_images=pages[1:])
                buf.seek(0)
                reader = PdfReader(buf)
                for p in reader.pages: writer.add_page(p)
                total_pages += len(reader.pages); used += len(img_buffer)
                log(f"🧾 拼版 {len(img_buffer)} 张 → {len(reader.pages)} 页")
                counter[0] = next_no
            except Exception as e:
                log(f"❌ 拼版失败: {e}")
            img_buffer.clear()

        for kind, path in items:
            if kind == "img":
                img_buffer.append(path)
            else:
                flush()
                try:
                    reader = PdfReader(path)
                    for p in reader.pages: writer.add_page(p)
                    total_pages += len(reader.pages); used += 1
                    log(f"✅ 已添加 PDF: {os.path.basename(path)} ({len(reader.pages)} 页)")
                except Exception as e:
                    log(f"❌ 失败: {path} -> {e}")
        flush()

    if total_pages == 0:
        log("没有生成任何页面"); return False

    with open(output_file, "wb") as f:
        writer.write(f)
    log(f"\n🎉 完成: {output_file} (共 {total_pages} 页, 来自 {used} 个文件)")
    return True
