"""
用法:
  # 普通合并
  python pdf_merge_cli.py -o out.pdf a.pdf cover.jpg b.pdf

  # 发票模式 (默认 6 张/页 2x3 拼到 A4) + 智能转向 + 裁白边 + 编号
  python pdf_merge_cli.py -o out.pdf --invoice ./invoices/*.jpg

  # 关闭 OCR (没装 tesseract 时, 仍按宽高比转向)
  python pdf_merge_cli.py -o out.pdf --invoice --no-ocr ./invoices/*.jpg
"""
import argparse, glob, sys
from pdf_utils import merge_files, PAGE_SIZES_MM


def expand(patterns):
    out = []
    for p in patterns:
        out.extend(sorted(glob.glob(p)) if any(c in p for c in "*?[") else [p])
    return out


def main():
    ap = argparse.ArgumentParser(description="PDF / 图片 拼接小工具 (发票增强)")
    ap.add_argument("-o", "--output", default="merged.pdf")
    ap.add_argument("--page", default="A4", choices=list(PAGE_SIZES_MM.keys()))
    ap.add_argument("--margin", type=float, default=5.0)
    ap.add_argument("--no-auto-orient", action="store_true")

    ap.add_argument("--invoice", action="store_true", help="启用发票模式")
    ap.add_argument("--per-page", type=int, default=6)
    ap.add_argument("--gap", type=float, default=3.0)
    ap.add_argument("--no-border", action="store_true")

    ap.add_argument("--no-smart-orient", action="store_true", help="关闭智能转向")
    ap.add_argument("--no-ocr",          action="store_true", help="不使用 OCR (只按宽高比)")
    ap.add_argument("--no-crop",         action="store_true", help="关闭自动裁白边")
    ap.add_argument("--crop-threshold",  type=int, default=240, help="白边亮度阈值 0-255")
    ap.add_argument("--crop-padding",    type=int, default=8,   help="裁后保留内边距(px)")
    ap.add_argument("--no-number",       action="store_true", help="不打编号")

    ap.add_argument("inputs", nargs="+")
    args = ap.parse_args()

    files = expand(args.inputs)
    if not files: print("未找到匹配文件"); sys.exit(1)

    ok = merge_files(
        files, args.output,
        page=args.page, margin_mm=args.margin,
        auto_orient=not args.no_auto_orient,
        invoice_mode=args.invoice,
        invoices_per_page=max(1, min(6, args.per_page)),
        invoice_gap_mm=args.gap,
        invoice_border=not args.no_border,
        smart_orient=not args.no_smart_orient,
        use_ocr=not args.no_ocr,
        auto_crop=not args.no_crop,
        crop_threshold=args.crop_threshold,
        crop_padding=args.crop_padding,
        number_invoices=not args.no_number,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
