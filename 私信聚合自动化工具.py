"""
私信聚合 1.4.8 — 自动化操作工具
功能：检测 UI 结构、自动点击消息、输入并发送消息
运行前自动检查并安装所有依赖

使用方法：
  1. 确保已安装 Python 3.8+（https://www.python.org/downloads/）
     安装时务必勾选 "Add Python to PATH"
  2. 双击运行本脚本，或在命令行执行：python 私信聚合自动化工具.py
"""

import subprocess
import sys
import os
import time
import json

# ============================================================
#  第一部分：环境自动安装
# ============================================================

REQUIRED_PACKAGES = {
    "pywinauto": "pywinauto",
    "pywin32": "pywin32",
    "Pillow": "Pillow",
}

TARGET_APP_TITLE = "私信聚合 1.4.8"

# 国内镜像源
MIRRORS = [
    "https://pypi.tuna.tsinghua.edu.cn/simple",   # 清华大学
    "https://mirrors.aliyun.com/pypi/simple",      # 阿里云
    "https://pypi.douban.com/simple",              # 豆瓣
]


def pip_install(pkg):
    """从国内镜像安装包，依次尝试直到成功"""
    for mirror in MIRRORS:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--upgrade", pkg, "-i", mirror],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            print(f"  [✓] {pkg} 安装成功 (源: {mirror})")
            return True
        except subprocess.CalledProcessError:
            continue
    # 兜底默认源
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", pkg],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        print(f"  [✓] {pkg} 安装成功 (源: 默认)")
        return True
    except subprocess.CalledProcessError:
        return False


def check_and_install_packages():
    """检查并自动安装缺失的依赖库"""
    print("=" * 60)
    print("  环境检查：正在检测依赖库（国内镜像安装）...")
    print("=" * 60)

    missing = []

    # 检查 pip 是否可用
    try:
        import pip
        print("  [✓] pip 已安装")
    except ImportError:
        print("  [✗] pip 未安装！请重新安装 Python 并勾选 pip")
        print("      下载地址: https://www.python.org/downloads/")
        input("\n按回车退出...")
        sys.exit(1)

    # 逐个检查依赖
    for display_name, package_name in REQUIRED_PACKAGES.items():
        try:
            if package_name == "pywin32":
                __import__("win32gui")
            elif package_name == "Pillow":
                __import__("PIL")
            else:
                __import__(package_name.replace("-", "_"))
            print(f"  [✓] {display_name} 已安装")
        except ImportError:
            print(f"  [✗] {display_name} 未安装，需要安装")
            missing.append(package_name)

    # 安装缺失的库
    if missing:
        print(f"\n正在从国内镜像安装 {len(missing)} 个缺失的库，请稍候...\n")
        for pkg in missing:
            print(f"  >>> 安装 {pkg} ...")
            if not pip_install(pkg):
                print(f"  [✗] {pkg} 安装失败！请手动执行：pip install {pkg} -i {MIRRORS[0]}")
                input("\n按回车退出...")
                sys.exit(1)

        # pywin32 安装后需要运行 post_install
        if "pywin32" in missing:
            try:
                scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
                post_install = os.path.join(scripts_dir, "pywin32_postinstall.py")
                if os.path.exists(post_install):
                    subprocess.check_call(
                        [sys.executable, post_install, "-install"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.STDOUT,
                    )
            except Exception:
                pass  # 非致命错误，继续

        print("\n  [✓] 所有依赖安装完成！\n")
    else:
        print("\n  [✓] 所有依赖均已就绪！\n")


# ============================================================
#  第二部分：UI 自动化核心功能
# ============================================================

def get_desktop():
    from pywinauto import Desktop
    return Desktop(backend="uia")


def get_app():
    from pywinauto import Application
    return Application(backend="uia")


def list_all_windows():
    """列出所有可见窗口"""
    desktop = get_desktop()
    windows = []
    for w in desktop.windows():
        title = w.window_text()
        if title.strip():
            windows.append((title, w.handle))
    return windows


def connect_by_title(title: str):
    """通过窗口标题连接应用"""
    app = get_app()
    app.connect(title=title)
    return app


def connect_by_path(exe_path: str):
    """通过 EXE 路径启动应用"""
    app = get_app()
    app.start(exe_path)
    time.sleep(3)
    return app


def find_controls(window, control_type=None, title=None, auto_id=None, class_name=None):
    """搜索指定条件的控件"""
    criteria = {}
    if control_type:
        criteria["control_type"] = control_type
    if title:
        criteria["title"] = title
    if auto_id:
        criteria["auto_id"] = auto_id
    if class_name:
        criteria["class_name"] = class_name
    try:
        return window.descendants(**criteria)
    except Exception:
        return []


def dump_control_tree(element, depth=0, max_depth=10, output_lines=None):
    """递归打印控件树"""
    if depth > max_depth:
        return
    indent = "  " * depth
    try:
        ctrl_type = element.element_info.control_type or "Unknown"
        title = element.window_text() or ""
        auto_id = element.element_info.automation_id or ""
        class_name = element.element_info.class_name or ""
        rect = element.rectangle()
        line = (
            f"{indent}[{ctrl_type}] "
            f'title="{title}" '
            f'auto_id="{auto_id}" '
            f'class="{class_name}" '
            f"rect=({rect.left},{rect.top},{rect.right},{rect.bottom})"
        )
        if output_lines is not None:
            output_lines.append(line)
        else:
            print(line)
    except Exception as e:
        err = f"{indent}[Error] {e}"
        if output_lines is not None:
            output_lines.append(err)
        else:
            print(err)
        return

    try:
        for child in element.children():
            dump_control_tree(child, depth + 1, max_depth, output_lines)
    except Exception:
        pass


def export_tree_json(element, depth=0, max_depth=8):
    """将控件树导出为 JSON"""
    if depth > max_depth:
        return None
    try:
        node = {
            "type": element.element_info.control_type,
            "title": element.window_text(),
            "auto_id": element.element_info.automation_id,
            "class_name": element.element_info.class_name,
            "rect": {
                "left": element.rectangle().left,
                "top": element.rectangle().top,
                "right": element.rectangle().right,
                "bottom": element.rectangle().bottom,
            },
            "children": [],
        }
    except Exception:
        return None
    try:
        for child in element.children():
            child_node = export_tree_json(child, depth + 1, max_depth)
            if child_node:
                node["children"].append(child_node)
    except Exception:
        pass
    return node


def find_chat_messages(window):
    """自动检测聊天相关控件"""
    results = {"message_list": [], "input_box": [], "send_button": []}

    for ctype in ["List", "ListView", "ListBox", "TreeView", "DataGrid"]:
        controls = find_controls(window, control_type=ctype)
        if controls:
            results["message_list"].extend(controls)

    edits = find_controls(window, control_type="Edit")
    results["input_box"] = edits

    all_buttons = find_controls(window, control_type="Button")
    keywords = ["发送", "Send", "submit", "确定"]
    for btn in all_buttons:
        try:
            btn_text = btn.window_text().lower()
            if any(kw.lower() in btn_text for kw in keywords):
                results["send_button"].append(btn)
        except Exception:
            pass

    return results


def click_element(element, double_click=False):
    """点击控件"""
    from pywinauto.keyboard import send_keys as _unused  # 确保模块加载
    element.wait("visible", timeout=5)
    if double_click:
        element.double_click_input()
        print(f"  [✓] 双击: {element.window_text()}")
    else:
        element.click_input()
        print(f"  [✓] 单击: {element.window_text()}")


def click_message_by_index(window, msg_index=0):
    """点击第 N 条消息"""
    for ctype in ["List", "ListView", "ListBox"]:
        lists = find_controls(window, control_type=ctype)
        for lst in lists:
            try:
                items = lst.children()
                if items and msg_index < len(items):
                    click_element(items[msg_index])
                    return True
            except Exception:
                continue

    list_items = find_controls(window, control_type="ListItem")
    if list_items and msg_index < len(list_items):
        click_element(list_items[msg_index])
        return True

    print(f"  [!] 未找到第 {msg_index} 条消息")
    return False


def type_and_send(window, text: str, press_enter=True):
    """输入文字并发送"""
    from pywinauto.keyboard import send_keys

    edits = find_controls(window, control_type="Edit")
    input_box = None
    for edit in edits:
        try:
            if edit.is_enabled():
                input_box = edit
                break
        except Exception:
            continue

    if not input_box:
        print("  [!] 未找到可用的输入框")
        return False

    click_element(input_box)
    time.sleep(0.3)
    send_keys("^a")
    time.sleep(0.1)

    try:
        input_box.set_edit_text(text)
    except Exception:
        send_keys(text, with_spaces=True)

    time.sleep(0.3)

    if press_enter:
        send_keys("{ENTER}")
        print(f"  [✓] 已发送: {text}")
    else:
        send_btns = find_controls(window, control_type="Button")
        for btn in send_btns:
            btn_text = btn.window_text().lower()
            if any(kw in btn_text for kw in ["发送", "send", "submit"]):
                click_element(btn)
                print(f"  [✓] 点击发送按钮，消息: {text}")
                return True
        send_keys("{ENTER}")
        print(f"  [✓] 按回车发送: {text}")

    return True


# ============================================================
#  第三部分：针对"私信聚合 1.4.8"的专用功能
# ============================================================

def connect_target_app():
    """连接到 私信聚合 1.4.8"""
    print(f"\n正在连接 [{TARGET_APP_TITLE}] ...")

    # 方式 1：窗口标题精确匹配
    try:
        app = connect_by_title(TARGET_APP_TITLE)
        win = app.window(title=TARGET_APP_TITLE)
        win.wait("exists visible", timeout=5)
        print(f"  [✓] 已连接: {TARGET_APP_TITLE}")
        return win
    except Exception:
        pass

    # 方式 2：窗口标题模糊匹配
    try:
        desktop = get_desktop()
        for w in desktop.windows():
            if "私信聚合" in w.window_text():
                app = connect_by_title(w.window_text())
                win = app.window(title=w.window_text())
                win.wait("exists visible", timeout=5)
                print(f"  [✓] 已连接: {w.window_text()}")
                return win
    except Exception:
        pass

    # 方式 3：找不到，提示用户
    print("  [!] 未找到 私信聚合 窗口")
    print("  请确保应用已启动，然后重试")
    return None


def scan_ui_structure(win):
    """扫描并展示 UI 结构"""
    print(f"\n{'=' * 60}")
    print(f"  正在扫描 [{TARGET_APP_TITLE}] 的 UI 结构...")
    print(f"{'=' * 60}\n")

    lines = []
    dump_control_tree(win, max_depth=8, output_lines=lines)

    for line in lines:
        print(line)

    # 保存文本文件
    with open("私信聚合_UI结构.txt", "w", encoding="utf-8") as f:
        f.write(f"私信聚合 1.4.8 — UI 控件树\n")
        f.write(f"扫描时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        for line in lines:
            f.write(line + "\n")
    print(f"\n  [✓] 已保存到: 私信聚合_UI结构.txt")

    # 保存 JSON
    tree = export_tree_json(win, max_depth=8)
    with open("私信聚合_UI结构.json", "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    print(f"  [✓] 已保存到: 私信聚合_UI结构.json")

    return lines


def auto_detect_controls(win):
    """自动检测聊天控件"""
    print(f"\n{'=' * 60}")
    print(f"  自动检测聊天控件")
    print(f"{'=' * 60}")

    results = find_chat_messages(win)

    print(f"\n  📋 消息列表控件: {len(results['message_list'])} 个")
    for i, c in enumerate(results["message_list"]):
        print(f"     [{i}] type={c.element_info.control_type} title=\"{c.window_text()[:50]}\"")

    print(f"\n  ✏️  输入框控件:   {len(results['input_box'])} 个")
    for i, c in enumerate(results["input_box"]):
        print(f"     [{i}] type={c.element_info.control_type} title=\"{c.window_text()[:50]}\"")

    print(f"\n  📤 发送按钮:     {len(results['send_button'])} 个")
    for i, c in enumerate(results["send_button"]):
        print(f"     [{i}] type={c.element_info.control_type} title=\"{c.window_text()[:50]}\"")

    # 按钮全量扫描
    all_buttons = find_controls(win, control_type="Button")
    print(f"\n  🔘 所有按钮:     {len(all_buttons)} 个")
    for i, c in enumerate(all_buttons):
        txt = c.window_text()[:40]
        print(f"     [{i}] \"{txt}\"")

    return results


def send_message_flow(win):
    """发送消息流程"""
    msg = input("\n  输入要发送的消息: ").strip()
    if not msg:
        print("  [!] 消息为空，取消")
        return

    method = input("  发送方式 [1=回车(默认) / 2=点击发送按钮]: ").strip()
    press_enter = method != "2"

    type_and_send(win, msg, press_enter=press_enter)


def batch_send_flow(win):
    """批量发送流程"""
    print("\n  批量发送模式（每行一条消息，输入空行结束）:")
    messages = []
    while True:
        line = input("    > ").strip()
        if not line:
            break
        messages.append(line)

    if not messages:
        print("  [!] 没有输入消息，取消")
        return

    interval = input("  每条间隔秒数 [默认2]: ").strip()
    interval = float(interval) if interval.replace(".", "").isdigit() else 2.0

    print(f"\n  开始批量发送 {len(messages)} 条消息（间隔 {interval}s）...\n")
    for i, msg in enumerate(messages, 1):
        print(f"  [{i}/{len(messages)}] {msg}")
        type_and_send(win, msg, press_enter=True)
        if i < len(messages):
            time.sleep(interval)

    print(f"\n  [✓] 批量发送完成！共 {len(messages)} 条")


def click_chat_flow(win):
    """点击聊天消息流程"""
    idx = input("\n  输入要点击的消息序号 [从0开始]: ").strip()
    if not idx.isdigit():
        print("  [!] 请输入数字")
        return
    click_message_by_index(win, int(idx))


def search_controls_flow(win):
    """搜索指定类型控件"""
    print("\n  常用控件类型: Button, Edit, List, ListItem, Text, CheckBox, ComboBox, Tab")
    ctype = input("  输入控件类型: ").strip()
    if not ctype:
        return
    controls = find_controls(win, control_type=ctype)
    print(f"\n  找到 {len(controls)} 个 [{ctype}] 控件:")
    for i, c in enumerate(controls):
        auto_id = c.element_info.automation_id
        txt = c.window_text()[:50]
        print(f"    [{i:3d}] title=\"{txt}\" auto_id=\"{auto_id}\"")


# ============================================================
#  第四部分：主菜单
# ============================================================

def print_banner():
    print()
    print("┌" + "─" * 56 + "┐")
    print("│" + " " * 10 + "私信聚合 1.4.8 自动化工具" + " " * 18 + "│")
    print("│" + " " * 12 + "UI 检测 · 消息点击 · 自动发送" + " " * 12 + "│")
    print("└" + "─" * 56 + "┘")


def main_menu():
    """主交互菜单"""
    win = None  # 当前连接的窗口

    while True:
        print_banner()
        print()
        print("  ── 连接 ──")
        print("  1. 连接到 私信聚合 1.4.8")
        print("  2. 列出系统所有窗口")
        print()
        print("  ── 检测 ──")
        print("  3. 扫描 UI 控件结构（完整树）")
        print("  4. 自动检测聊天相关控件")
        print("  5. 搜索指定类型控件")
        print()
        print("  ── 操作 ──")
        print("  6. 点击指定序号的聊天消息")
        print("  7. 输入并发送单条消息")
        print("  8. 批量发送消息")
        print()
        print("  0. 退出")
        print()

        choice = input("  请选择 [0-8]: ").strip()

        if choice == "1":
            win = connect_target_app()

        elif choice == "2":
            print()
            windows = list_all_windows()
            print(f"  {'─' * 50}")
            for i, (title, handle) in enumerate(windows, 1):
                marker = " ◀" if "私信聚合" in title else ""
                print(f"  [{i:3d}] {title}{marker}")
            print(f"  {'─' * 50}")
            print(f"  共 {len(windows)} 个窗口")

        elif choice == "3":
            if not win:
                win = connect_target_app()
            if win:
                scan_ui_structure(win)

        elif choice == "4":
            if not win:
                win = connect_target_app()
            if win:
                auto_detect_controls(win)

        elif choice == "5":
            if not win:
                win = connect_target_app()
            if win:
                search_controls_flow(win)

        elif choice == "6":
            if not win:
                win = connect_target_app()
            if win:
                click_chat_flow(win)

        elif choice == "7":
            if not win:
                win = connect_target_app()
            if win:
                send_message_flow(win)

        elif choice == "8":
            if not win:
                win = connect_target_app()
            if win:
                batch_send_flow(win)

        elif choice == "0":
            print("\n  再见！\n")
            break

        else:
            print("  [!] 无效选择，请输入 0-8")

        input("\n  按回车继续...")


# ============================================================
#  入口
# ============================================================

if __name__ == "__main__":
    os.system("chcp 65001 >nul 2>&1")  # 设置 UTF-8 编码

    print()
    print("=" * 60)
    print("  私信聚合 1.4.8 自动化工具 — 环境初始化")
    print("=" * 60)

    # 第一步：检查并安装依赖
    check_and_install_packages()

    # 第二步：启动主菜单
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n  已中断，退出。")
    except Exception as e:
        print(f"\n  [!] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车退出...")
