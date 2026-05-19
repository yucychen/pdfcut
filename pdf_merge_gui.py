"""
PDF / 图片 拼接小工具 - GUI (发票增强)
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pdf_utils import merge_files, is_supported, SUPPORTED_EXTS, PAGE_SIZES_MM


class App:
    def __init__(self, root):
        self.root = root
        root.title("PDF / 图片 拼接小工具")
        root.geometry("820x720")

        frame = ttk.Frame(root, padding=10); frame.pack(fill=tk.BOTH, expand=True)

        # ---- 普通设置 ----
        cfg = ttk.LabelFrame(frame, text="图片转 PDF 设置", padding=8)
        cfg.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(cfg, text="纸张:").grid(row=0, column=0, padx=4, sticky=tk.W)
        self.page_var = tk.StringVar(value="A4")
        ttk.Combobox(cfg, textvariable=self.page_var, width=10,
                     values=list(PAGE_SIZES_MM.keys()), state="readonly"
                     ).grid(row=0, column=1, padx=4)
        ttk.Label(cfg, text="边距(mm):").grid(row=0, column=2, padx=4, sticky=tk.W)
        self.margin_var = tk.DoubleVar(value=5.0)
        ttk.Spinbox(cfg, from_=0, to=50, increment=1, width=6,
                    textvariable=self.margin_var).grid(row=0, column=3, padx=4)
        self.auto_orient_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(cfg, text="横图自动横向页面",
                        variable=self.auto_orient_var
                        ).grid(row=0, column=4, padx=10, sticky=tk.W)

        # ---- 发票模式 ----
        inv = ttk.LabelFrame(frame, text="📑 发票模式", padding=8)
        inv.pack(fill=tk.X, pady=(0, 8))

        self.invoice_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(inv, text="启用发票模式",
                        variable=self.invoice_var, command=self._toggle
                        ).grid(row=0, column=0, padx=4, sticky=tk.W)

        ttk.Label(inv, text="每页张数:").grid(row=0, column=1, sticky=tk.W)
        self.per_page_var = tk.IntVar(value=6)
        self.per_page_spin = ttk.Spinbox(inv, from_=1, to=6, increment=1, width=5,
                                         textvariable=self.per_page_var)
        self.per_page_spin.grid(row=0, column=2, padx=4)

        ttk.Label(inv, text="间距(mm):").grid(row=0, column=3, sticky=tk.W)
        self.gap_var = tk.DoubleVar(value=3.0)
        self.gap_spin = ttk.Spinbox(inv, from_=0, to=30, increment=1, width=5,
                                    textvariable=self.gap_var)
        self.gap_spin.grid(row=0, column=4, padx=4)

        self.border_var = tk.BooleanVar(value=True)
        self.border_chk = ttk.Checkbutton(inv, text="格子边框",
                                          variable=self.border_var)
        self.border_chk.grid(row=0, column=5, padx=10, sticky=tk.W)

        self.smart_var = tk.BooleanVar(value=True)
        self.smart_chk = ttk.Checkbutton(inv, text="🧠 智能识别方向",
                                         variable=self.smart_var)
        self.smart_chk.grid(row=1, column=0, padx=4, sticky=tk.W)

        self.ocr_var = tk.BooleanVar(value=True)
        self.ocr_chk = ttk.Checkbutton(inv, text="使用 OCR (需安装 Tesseract)",
                                       variable=self.ocr_var)
        self.ocr_chk.grid(row=1, column=1, columnspan=2, padx=4, sticky=tk.W)

        self.crop_var = tk.BooleanVar(value=True)
        self.crop_chk = ttk.Checkbutton(inv, text="✂️ 自动裁白边",
                                        variable=self.crop_var)
        self.crop_chk.grid(row=1, column=3, padx=4, sticky=tk.W)

        self.num_var = tk.BooleanVar(value=True)
        self.num_chk = ttk.Checkbutton(inv, text="🔢 右下角编号",
                                       variable=self.num_var)
        self.num_chk.grid(row=1, column=4, columnspan=2, padx=4, sticky=tk.W)

        ttk.Label(inv, text="(发票模式只对图片生效, PDF 原样保留)",
                  foreground="#888").grid(row=2, column=0, columnspan=6,
                                          padx=4, sticky=tk.W)
        self._toggle()

        # ---- 文件列表 ----
        ttk.Label(frame, text="待合并文件 (按列表顺序):").pack(anchor=tk.W)
        lf = ttk.Frame(frame); lf.pack(fill=tk.BOTH, expand=True, pady=5)
        self.listbox = tk.Listbox(lf, selectmode=tk.EXTENDED)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(lf, command=self.listbox.yview); sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=sb.set)

        btns = ttk.Frame(frame); btns.pack(fill=tk.X, pady=5)
        ttk.Button(btns, text="➕ 添加 PDF",  command=self.add_pdfs).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="🖼️ 添加图片", command=self.add_images).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="➕ 添加任意",  command=self.add_any).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="➖ 删除",      command=self.remove).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="🔼 上移",      command=lambda: self.move(-1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="🔽 下移",      command=lambda: self.move(1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="🧹 清空",      command=lambda: self.listbox.delete(0, tk.END)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="🚀 开始合并",  command=self.merge).pack(side=tk.RIGHT, padx=2)

        ttk.Label(frame, text="日志:").pack(anchor=tk.W)
        self.log = tk.Text(frame, height=12, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=False)

        self.status = tk.StringVar(value="就绪")
        ttk.Label(root, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W
                  ).pack(fill=tk.X, side=tk.BOTTOM)

    def _toggle(self):
        st = "normal" if self.invoice_var.get() else "disabled"
        for w in (self.per_page_spin, self.gap_spin, self.border_chk,
                  self.smart_chk, self.ocr_chk, self.crop_chk, self.num_chk):
            w.config(state=st)

    def add_pdfs(self):
        self._add(filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")]))
    def add_images(self):
        self._add(filedialog.askopenfilenames(filetypes=[
            ("图片", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp")]))
    def add_any(self):
        types = " ".join(f"*{e}" for e in SUPPORTED_EXTS)
        self._add(filedialog.askopenfilenames(filetypes=[
            ("PDF 或 图片", types), ("所有文件", "*.*")]))
    def _add(self, files):
        for f in files:
            if is_supported(f): self.listbox.insert(tk.END, f)
            else: self._log(f"⚠️ 不支持: {f}")
    def remove(self):
        for i in reversed(self.listbox.curselection()): self.listbox.delete(i)
    def move(self, d):
        sel = list(self.listbox.curselection())
        if not sel: return
        if d == -1 and sel[0] == 0: return
        if d == 1 and sel[-1] == self.listbox.size() - 1: return
        items = list(self.listbox.get(0, tk.END))
        for i in (sel if d == -1 else reversed(sel)):
            items[i], items[i + d] = items[i + d], items[i]
        self.listbox.delete(0, tk.END)
        for it in items: self.listbox.insert(tk.END, it)
        for i in sel: self.listbox.selection_set(i + d)

    def merge(self):
        files = list(self.listbox.get(0, tk.END))
        if not files: messagebox.showwarning("提示", "请先添加文件。"); return
        out = filedialog.asksaveasfilename(defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")], initialfile="merged.pdf")
        if not out: return

        self._clear_log()
        try:
            ok = merge_files(
                files, out,
                page=self.page_var.get(),
                margin_mm=float(self.margin_var.get()),
                auto_orient=self.auto_orient_var.get(),
                invoice_mode=self.invoice_var.get(),
                invoices_per_page=int(self.per_page_var.get()),
                invoice_gap_mm=float(self.gap_var.get()),
                invoice_border=self.border_var.get(),
                smart_orient=self.smart_var.get(),
                use_ocr=self.ocr_var.get(),
                auto_crop=self.crop_var.get(),
                number_invoices=self.num_var.get(),
                log=self._log,
            )
            if ok:
                self.status.set(f"完成: {out}")
                messagebox.showinfo("成功", f"已生成: {out}")
            else: self.status.set("未生成内容")
        except Exception as e:
            messagebox.showerror("错误", str(e)); self.status.set("失败")

    def _log(self, msg):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, str(msg) + "\n"); self.log.see(tk.END)
        self.log.config(state=tk.DISABLED); self.root.update_idletasks()
    def _clear_log(self):
        self.log.config(state=tk.NORMAL); self.log.delete("1.0", tk.END)
        self.log.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk(); App(root); root.mainloop()
