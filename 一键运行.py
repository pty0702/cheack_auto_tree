"""
私信聚合 自动化工具 — 单文件版
复制这一个文件到目标电脑即可运行，自动安装依赖。

使用步骤：
  1. 安装 Python 3.8+（勾选 Add to PATH）
  2. 把本文件复制到目标电脑
  3. 双击运行，或命令行执行：python 一键运行.py
"""

# ============================================================
#  自动安装依赖（使用国内镜像）
# ============================================================
import subprocess, sys

# 国内镜像源（按速度排序，可自行切换）
MIRRORS = [
    "https://pypi.tuna.tsinghua.edu.cn/simple",   # 清华大学（推荐）
    "https://mirrors.aliyun.com/pypi/simple",      # 阿里云
    "https://pypi.douban.com/simple",              # 豆瓣
]

def ensure_package(import_name, pip_name=None):
    """确保包已安装，没有就从镜像自动装"""
    pip_name = pip_name or import_name
    try:
        __import__(import_name)
    except ImportError:
        print(f"  正在安装 {pip_name} ...")
        # 依次尝试镜像源，直到成功
        for mirror in MIRRORS:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pip_name, "-i", mirror],
                    stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
                )
                print(f"  [OK] {pip_name} (源: {mirror})")
                return
            except subprocess.CalledProcessError:
                continue
        # 兜底：用默认源
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pip_name],
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
        print(f"  [OK] {pip_name} (源: 默认)")

print("=" * 50)
print("  检查依赖（国内镜像安装）...")
print("=" * 50)
ensure_package("pywinauto")
print("  所有依赖就绪!\n")

# ============================================================
#  核心功能
# ============================================================
import time, json, os

os.system("chcp 65001 >nul 2>&1")


def list_windows():
    """列出所有可见窗口，返回 [(title, handle), ...]"""
    from pywinauto import Desktop
    desktop = Desktop(backend="uia")
    result = []
    for w in desktop.windows():
        title = w.window_text()
        if title.strip():
            result.append((title, w.handle))
    return result


def select_window():
    """交互式选择窗口，返回连接好的 win 对象"""
    from pywinauto import Application

    windows = list_windows()
    if not windows:
        print("  [!] 没有找到任何窗口")
        return None

    print()
    print(f"  {'序号':<6}窗口标题")
    print(f"  {'─' * 50}")
    for i, (title, handle) in enumerate(windows, 1):
        print(f"  {i:<6}{title}")
    print(f"  {'─' * 50}")

    choice = input("\n  输入序号选择窗口: ").strip()
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(windows):
        print("  [!] 无效序号")
        return None

    title, handle = windows[int(choice) - 1]
    print(f"  正在连接: {title}")

    try:
        app = Application(backend="uia").connect(handle=handle)
        win = app.window(handle=handle)
        win.wait("exists visible", timeout=5)
        print(f"  [OK] 已连接")
        return win
    except Exception as e:
        print(f"  [!] 连接失败: {e}")
        return None


def connect(title):
    """连接窗口，返回 pywinauto window 对象"""
    from pywinauto import Desktop, Application

    # 精确匹配
    try:
        app = Application(backend="uia").connect(title=title)
        win = app.window(title=title)
        win.wait("exists visible", timeout=5)
        return win
    except Exception:
        pass

    # 模糊匹配
    for w in Desktop(backend="uia").windows():
        if title in w.window_text():
            app = Application(backend="uia").connect(title=w.window_text())
            win = app.window(title=w.window_text())
            win.wait("exists visible", timeout=5)
            return win

    raise RuntimeError(f"找不到窗口: {title}")


def dump_tree(win, depth=0, max_depth=8):
    """打印控件树"""
    if depth > max_depth:
        return
    indent = "  " * depth
    try:
        t = win.element_info.control_type or "?"
        title = win.window_text() or ""
        aid = win.element_info.automation_id or ""
        cls = win.element_info.class_name or ""
        r = win.rectangle()
        print(f"{indent}[{t}] title=\"{title}\" id=\"{aid}\" class=\"{cls}\" rect=({r.left},{r.top},{r.right},{r.bottom})")
    except Exception as e:
        print(f"{indent}[Error] {e}")
        return
    try:
        for child in win.children():
            dump_tree(child, depth + 1, max_depth)
    except Exception:
        pass


def find(win, **kwargs):
    """搜索控件，支持 title_contains 模糊匹配"""
    title_contains = kwargs.pop("title_contains", None)
    try:
        controls = win.descendants(**kwargs)
    except Exception:
        return []
    if title_contains:
        kw = title_contains.lower()
        controls = [c for c in controls if kw in (c.window_text() or "").lower()]
    return controls


def get_list_items(win, index=0):
    """获取第 N 个列表的子项"""
    for ctype in ["List", "ListView", "ListBox"]:
        lists = find(win, control_type=ctype)
        if lists and index < len(lists):
            try:
                return lists[index].children()
            except Exception:
                continue
    return []


def find_input_box(win):
    """找到第一个可用的输入框"""
    for edit in find(win, control_type="Edit"):
        try:
            if edit.is_enabled():
                return edit
        except Exception:
            continue
    return None


def send_msg(win, text):
    """输入文字并按回车发送"""
    from pywinauto.keyboard import send_keys
    box = find_input_box(win)
    if not box:
        print("  [!] 找不到输入框")
        return False
    box.click_input()
    time.sleep(0.2)
    send_keys("^a")
    time.sleep(0.1)
    try:
        box.set_edit_text(text)
    except Exception:
        send_keys(text, with_spaces=True)
    time.sleep(0.2)
    send_keys("{ENTER}")
    print(f"  [OK] 已发送: {text}")
    return True


def export_json(win, filename="ui_tree.json", max_depth=8):
    """导出控件树为 JSON"""
    def to_dict(elem, d=0):
        if d > max_depth:
            return None
        try:
            node = {
                "type": elem.element_info.control_type,
                "title": elem.window_text(),
                "auto_id": elem.element_info.automation_id,
                "class": elem.element_info.class_name,
                "children": []
            }
        except Exception:
            return None
        try:
            for child in elem.children():
                c = to_dict(child, d + 1)
                if c:
                    node["children"].append(c)
        except Exception:
            pass
        return node

    data = to_dict(win)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [OK] 已保存: {filename}")


# ============================================================
#  主菜单
# ============================================================
def main():
    win = None

    while True:
        print()
        print("=" * 50)
        print("  控件树检测 & 自动化工具")
        print("=" * 50)
        if win:
            try:
                print(f"  当前窗口: {win.window_text()}")
            except Exception:
                print(f"  当前窗口: [已断开]")
                win = None
        print()
        print("  1. 选择窗口")
        print("  2. 打印控件树")
        print("  3. 搜索控件（按类型）")
        print("  4. 搜索控件（按标题关键字）")
        print("  5. 获取列表项并点击")
        print("  6. 发送消息（输入文字+回车）")
        print("  7. 导出控件树为 JSON")
        print("  0. 退出")
        print("=" * 50)

        choice = input("\n  选择 [0-7]: ").strip()

        if choice == "1":
            win = select_window()

        elif choice == "2":
            if not win:
                print("  [!] 请先选 1 选择窗口")
                continue
            depth = input("  深度 [默认8]: ").strip()
            dump_tree(win, max_depth=int(depth) if depth.isdigit() else 8)

        elif choice == "3":
            if not win:
                print("  [!] 请先选 1 选择窗口")
                continue
            print("  类型: Button, Edit, List, ListItem, Text, CheckBox, ComboBox, Tab")
            ct = input("  控件类型: ").strip()
            if ct:
                results = find(win, control_type=ct)
                print(f"  找到 {len(results)} 个:")
                for i, c in enumerate(results):
                    print(f"    [{i}] \"{c.window_text()}\" id=\"{c.element_info.automation_id}\"")

        elif choice == "4":
            if not win:
                print("  [!] 请先选 1 选择窗口")
                continue
            kw = input("  标题关键字: ").strip()
            if kw:
                results = find(win, title_contains=kw)
                print(f"  找到 {len(results)} 个:")
                for i, c in enumerate(results):
                    print(f"    [{i}] type={c.element_info.control_type} title=\"{c.window_text()}\"")

        elif choice == "5":
            if not win:
                print("  [!] 请先选 1 选择窗口")
                continue
            items = get_list_items(win)
            print(f"  列表项: {len(items)} 个")
            for i, item in enumerate(items[:20]):
                print(f"    [{i}] {item.window_text()}")
            idx = input("  点击第几个 [输入数字]: ").strip()
            if idx.isdigit() and int(idx) < len(items):
                items[int(idx)].click_input()
                print(f"  [OK] 已点击第 {idx} 项")

        elif choice == "6":
            if not win:
                print("  [!] 请先选 1 选择窗口")
                continue
            text = input("  要发送的文字: ").strip()
            if text:
                send_msg(win, text)

        elif choice == "7":
            if not win:
                print("  [!] 请先选 1 选择窗口")
                continue
            fname = input("  文件名 [默认 ui_tree.json]: ").strip() or "ui_tree.json"
            export_json(win, fname)

        elif choice == "0":
            print("  再见!")
            break

        input("\n  按回车继续...")


if __name__ == "__main__":
    main()
