# 📎 pdfcut — PDF / 图片 拼接小工具

一个轻量、跨平台的 PDF 与图片合并工具，支持 **图形界面** 和 **命令行**，并内置 **发票模式**：一张 A4 自动拼 ≤ 6 张发票，附带智能方向识别、自动裁白边、自动编号等增强功能。

## ✨ 功能

- 📄 PDF + 图片 (JPG/PNG/BMP/TIFF/WEBP) 混合按顺序合并
- 📐 图片自适应 A4 / A5 / Letter，等比缩放 + 居中 + 可调边距
- 🔄 横图自动转横向页面、EXIF 方向校正
- 📑 **发票模式**：1-6 张/页拼到 A4（默认 2×3 共 6 张），自动分页
  - 🧠 **智能方向识别**（基于 Tesseract OSD，未安装时降级为宽高比启发式）
  - ✂️ **自动裁白边**：扫描件四周白边自动去除
  - 🔢 **右下角自动编号**：跨页连续，便于报销对账
  - 🟦 浅灰格子边框，便于打印后裁剪
- 📦 PyInstaller 一键打包成单文件 exe

## 📦 安装

```bash
pip install -r requirements.txt
# 可选: 智能方向识别 (推荐)
pip install pytesseract
# 并安装 Tesseract 引擎:
#   Windows: https://github.com/UB-Mannheim/tesseract/wiki
#   macOS:   brew install tesseract
#   Linux:   sudo apt install tesseract-ocr
```

## 🚀 使用

### GUI（推荐）

```bash
python pdf_merge_gui.py
```

操作步骤：添加 PDF / 图片 → 调整顺序 → （可选）开启「📑 发票模式」并调整参数 → 点击「🚀 开始合并」。

### 命令行

```bash
# 普通合并
python pdf_merge_cli.py -o out.pdf a.pdf cover.jpg b.pdf

# 发票模式: 6 张/页 + 智能转向 + 裁白边 + 编号
python pdf_merge_cli.py -o invoices.pdf --invoice ./invoices/*.jpg

# 4 张/页, 不要边框, 关闭 OCR
python pdf_merge_cli.py -o invoices.pdf --invoice --per-page 4 --no-border --no-ocr ./invoices/*.jpg

# 报销封面 + 发票 + 总结页
python pdf_merge_cli.py -o report.pdf --invoice cover.pdf ./invoices/*.jpg summary.pdf
```

#### CLI 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `-o, --output` | 输出文件 | `merged.pdf` |
| `--page` | 纸张：A4 / A4_LAND / A5 / LETTER / AUTO | `A4` |
| `--margin` | 页边距 (mm) | `5` |
| `--no-auto-orient` | 禁用横图自动转横向 | - |
| `--invoice` | 启用发票模式 | 关 |
| `--per-page` | 发票模式每页张数 (1–6) | `6` |
| `--gap` | 发票格子间距 (mm) | `3` |
| `--no-border` | 关闭格子边框 | - |
| `--no-smart-orient` | 关闭智能转向 | - |
| `--no-ocr` | 不使用 OCR (仅按宽高比) | - |
| `--no-crop` | 关闭自动裁白边 | - |
| `--crop-threshold` | 白边亮度阈值 0-255 | `240` |
| `--crop-padding` | 裁后保留内边距 (px) | `8` |
| `--no-number` | 不打编号 | - |

## 📦 打包为可执行文件

```bash
pip install pyinstaller
python build_exe.py            # 打包 GUI -> dist/PDFMerger
python build_exe.py cli        # 打包命令行 -> dist/PDFMerger_cli
```

> 注：`pytesseract` 仅是 Python 包装；OCR 功能需目标机器单独安装 Tesseract 引擎，否则会自动降级为宽高比启发式（不影响主功能）。

## 🗂️ 项目结构

```
pdfcut/
├── pdf_utils.py        # 核心合并 / 发票拼版逻辑
├── image_ops.py        # 自动裁白边 + 智能方向识别
├── pdf_merge_cli.py    # 命令行入口
├── pdf_merge_gui.py    # Tkinter GUI 入口
├── build_exe.py        # PyInstaller 打包脚本
├── requirements.txt
└── README.md
```

## 📜 License

MIT
