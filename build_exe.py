"""
一键打包成单文件可执行程序
用法:
    python build_exe.py            # 打包 GUI
    python build_exe.py cli        # 打包命令行版本
"""
import os, sys, shutil, subprocess

APP_NAME = "PDFMerger"
GUI_ENTRY = "pdf_merge_gui.py"
CLI_ENTRY = "pdf_merge_cli.py"


def build(entry, name, windowed=True):
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile",
        "--name", name,
        "--hidden-import", "PIL._tkinter_finder",
        "--collect-submodules", "pypdf",
        entry,
    ]
    if windowed:
        args.insert(args.index("--onefile") + 1, "--windowed")
    print(">>", " ".join(args))
    subprocess.check_call(args)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "gui"
    for d in ("build", "dist"):
        if os.path.isdir(d): shutil.rmtree(d)
    for f in os.listdir("."):
        if f.endswith(".spec"): os.remove(f)

    if mode == "cli":
        build(CLI_ENTRY, APP_NAME + "_cli", windowed=False)
    else:
        build(GUI_ENTRY, APP_NAME, windowed=True)

    print("\n✅ 打包完成, 产物在 dist/ 目录")


if __name__ == "__main__":
    main()
