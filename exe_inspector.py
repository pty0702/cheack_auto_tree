"""
EXE 应用 UI 结构检测与自动化操作工具
功能：
  1. 列出系统中所有可见窗口
  2. 检测指定 EXE 的 UI 控件树结构
  3. 自动点击聊天消息、输入并发送消息
依赖：pip install pywinauto
"""

import sys
import time
import json
from pywinauto import Desktop, Application
from pywinauto.keyboard import send_keys


# ============================================================
#  1. 列出所有可见窗口
# ============================================================
def list_all_windows():
    """列出系统中所有可见窗口，返回 [(title, handle), ...]"""
    desktop = Desktop(backend="uia")
    windows = []
    for w in desktop.windows():
        title = w.window_text()
        if title.strip():
            windows.append((title, w.handle))
    return windows


def print_all_windows():
    """打印所有可见窗口"""
    print("=" * 60)
    print("  系统中所有可见窗口")
    print("=" * 60)
    windows = list_all_windows()
    for i, (title, handle) in enumerate(windows, 1):
        print(f"  [{i:3d}] handle={handle}  |  {title}")
    print(f"\n共 {len(windows)} 个窗口")
    return windows


# ============================================================
#  2. 连接到目标应用（两种方式）
# ============================================================
def connect_by_title(title: str):
    """通过窗口标题连接应用"""
    app = Application(backend="uia").connect(title=title)
    return app


def connect_by_path(exe_path: str):
    """通过 EXE 路径启动并连接应用"""
    app = Application(backend="uia").start(exe_path)
    time.sleep(2)  # 等待应用启动
    return app


# ============================================================
#  3. 递归打印控件树（核心功能）
# ============================================================
def dump_control_tree(element, depth=0, max_depth=10, file=None):
    """
    递归打印 UI 控件树
    参数:
        element:  pywinauto 控件对象
        depth:    当前缩进层级
        max_depth: 最大递归深度
        file:     输出到文件（None 则打印到终端）
    """
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

        if file:
            file.write(line + "\n")
        else:
            print(line)
    except Exception as e:
        if file:
            file.write(f"{indent}[Error] {e}\n")
        else:
            print(f"{indent}[Error] {e}")
        return

    # 递归子控件
    try:
        children = element.children()
        for child in children:
            dump_control_tree(child, depth + 1, max_depth, file)
    except Exception:
        pass


def inspect_app(window_title: str, max_depth=10, save_to_file="ui_tree.txt"):
    """
    检测并打印指定窗口的完整 UI 控件树
    参数:
        window_title: 窗口标题（部分匹配即可）
        max_depth:    递归深度
        save_to_file: 保存到文件名（None 则不保存）
    """
    app = connect_by_title(window_title)
    main_window = app.window(title=window_title)
    main_window.wait("exists visible", timeout=10)

    print(f"\n{'=' * 60}")
    print(f"  检测窗口: {window_title}")
    print(f"{'=' * 60}\n")

    # 打印到终端
    dump_control_tree(main_window, max_depth=max_depth)

    # 保存到文件
    if save_to_file:
        with open(save_to_file, "w", encoding="utf-8") as f:
            dump_control_tree(main_window, max_depth=max_depth, file=f)
        print(f"\n[✓] 控件树已保存到: {save_to_file}")

    return main_window


# ============================================================
#  4. 按条件搜索控件
# ============================================================
def find_controls(window, control_type=None, title=None, auto_id=None, class_name=None):
    """
    在窗口中搜索满足条件的控件
    返回匹配的控件列表
    """
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
        controls = window.descendants(**criteria)
        return controls
    except Exception as e:
        print(f"[!] 搜索失败: {e}")
        return []


def find_chat_messages(window):
    """
    尝试自动找到聊天消息列表控件
    常见的消息列表控件类型: List, ListView, ListBox, TreeView
    也可以通过 Edit 控件找到消息输入框
    """
    results = {"message_list": [], "input_box": [], "send_button": []}

    # 查找消息列表（常见的控件类型）
    for ctype in ["List", "ListView", "ListBox", "TreeView", "DataGrid"]:
        controls = find_controls(window, control_type=ctype)
        if controls:
            results["message_list"].extend(controls)

    # 查找输入框（Edit 控件）
    edits = find_controls(window, control_type="Edit")
    results["input_box"] = edits

    # 查找发送按钮
    for title_keyword in ["发送", "Send", "submit", "确定"]:
        buttons = find_controls(window, control_type="Button", title=title_keyword)
        if buttons:
            results["send_button"].extend(buttons)

    return results


# ============================================================
#  5. 自动化操作：点击、输入、发送
# ============================================================
def click_element(element, double_click=False):
    """点击指定控件"""
    element.wait("visible", timeout=5)
    if double_click:
        element.double_click_input()
        print(f"[✓] 双击: {element.window_text()}")
    else:
        element.click_input()
        print(f"[✓] 单击: {element.window_text()}")


def click_by_index(window, control_type, index=0, double_click=False):
    """按索引点击第 N 个指定类型的控件"""
    controls = find_controls(window, control_type=control_type)
    if not controls:
        print(f"[!] 未找到类型为 {control_type} 的控件")
        return False
    if index >= len(controls):
        print(f"[!] 索引 {index} 超出范围（共 {len(controls)} 个控件）")
        return False
    click_element(controls[index], double_click)
    return True


def click_message_by_index(window, msg_index=0):
    """点击聊天列表中第 N 条消息"""
    # 先尝试找到列表控件
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

    # 如果没找到列表，尝试直接找 ListItem
    list_items = find_controls(window, control_type="ListItem")
    if list_items and msg_index < len(list_items):
        click_element(list_items[msg_index])
        return True

    print(f"[!] 未找到第 {msg_index} 条消息")
    return False


def type_and_send(window, text: str, press_enter=True):
    """
    在输入框中输入文字并发送
    参数:
        window: 目标窗口
        text: 要输入的文字
        press_enter: True=按回车发送, False=尝试点击发送按钮
    """
    # 找到输入框
    edits = find_controls(window, control_type="Edit")

    # 优先选择可写入的 Edit 控件
    input_box = None
    for edit in edits:
        try:
            if edit.is_enabled():
                input_box = edit
                break
        except Exception:
            continue

    if not input_box:
        print("[!] 未找到可用的输入框")
        return False

    # 点击输入框获取焦点
    click_element(input_box)
    time.sleep(0.3)

    # 清空现有内容并输入新文字
    send_keys("^a")  # Ctrl+A 全选
    time.sleep(0.1)

    # 使用 set_edit_text 输入（支持中文）
    try:
        input_box.set_edit_text(text)
    except Exception:
        # 退回到键盘输入
        send_keys(text, with_spaces=True)

    time.sleep(0.3)

    if press_enter:
        send_keys("{ENTER}")
        print(f"[✓] 已发送消息: {text}")
    else:
        # 尝试点击发送按钮
        send_buttons = find_controls(window, control_type="Button")
        for btn in send_buttons:
            btn_text = btn.window_text().lower()
            if any(kw in btn_text for kw in ["发送", "send", "submit"]):
                click_element(btn)
                print(f"[✓] 已点击发送按钮，消息: {text}")
                return True
        # 没找到按钮就按回车
        send_keys("{ENTER}")
        print(f"[✓] 已按回车发送: {text}")

    return True


# ============================================================
#  6. JSON 导出控件树（便于程序化分析）
# ============================================================
def export_tree_json(element, depth=0, max_depth=8):
    """将控件树导出为 JSON 结构"""
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


def save_tree_json(window_title, filename="ui_tree.json", max_depth=8):
    """将控件树保存为 JSON 文件"""
    app = connect_by_title(window_title)
    win = app.window(title=window_title)
    win.wait("exists visible", timeout=10)

    tree = export_tree_json(win, max_depth=max_depth)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    print(f"[✓] JSON 控件树已保存到: {filename}")
    return tree


# ============================================================
#  7. 交互式菜单
# ============================================================
def interactive_menu():
    """交互式操作菜单"""
    window_title = None
    main_window = None

    while True:
        print("\n" + "=" * 50)
        print("  EXE UI 自动化工具")
        print("=" * 50)
        print("  1. 列出所有窗口")
        print("  2. 检测指定窗口的 UI 结构")
        print("  3. 导出控件树为 JSON")
        print("  4. 搜索指定类型控件")
        print("  5. 自动检测聊天相关控件")
        print("  6. 点击指定索引的消息")
        print("  7. 输入并发送消息")
        print("  8. 通过路径启动 EXE")
        print("  0. 退出")
        print("=" * 50)

        choice = input("\n请选择操作 [0-8]: ").strip()

        if choice == "1":
            print_all_windows()

        elif choice == "2":
            title = input("输入窗口标题（支持部分匹配）: ").strip()
            depth = input("递归深度 [默认10]: ").strip()
            depth = int(depth) if depth.isdigit() else 10
            try:
                main_window = inspect_app(title, max_depth=depth)
                window_title = title
            except Exception as e:
                print(f"[!] 连接失败: {e}")

        elif choice == "3":
            if not window_title:
                window_title = input("输入窗口标题: ").strip()
            fname = input("JSON 文件名 [默认 ui_tree.json]: ").strip() or "ui_tree.json"
            try:
                save_tree_json(window_title, fname)
            except Exception as e:
                print(f"[!] 导出失败: {e}")

        elif choice == "4":
            if not main_window:
                print("[!] 请先执行操作 2 连接窗口")
                continue
            print("控件类型: Button, Edit, List, ListItem, Text, CheckBox, ComboBox, ...")
            ctype = input("输入控件类型: ").strip()
            controls = find_controls(main_window, control_type=ctype)
            print(f"\n找到 {len(controls)} 个 {ctype} 控件:")
            for i, c in enumerate(controls):
                print(f"  [{i}] title=\"{c.window_text()}\" auto_id=\"{c.element_info.automation_id}\"")

        elif choice == "5":
            if not main_window:
                print("[!] 请先执行操作 2 连接窗口")
                continue
            results = find_chat_messages(main_window)
            print("\n--- 自动检测结果 ---")
            for key, controls in results.items():
                print(f"\n{key}: {len(controls)} 个")
                for i, c in enumerate(controls):
                    print(f"  [{i}] title=\"{c.window_text()}\" type=\"{c.element_info.control_type}\"")

        elif choice == "6":
            if not main_window:
                print("[!] 请先执行操作 2 连接窗口")
                continue
            idx = input("输入消息索引 [从0开始]: ").strip()
            if idx.isdigit():
                click_message_by_index(main_window, int(idx))

        elif choice == "7":
            if not main_window:
                print("[!] 请先执行操作 2 连接窗口")
                continue
            text = input("输入要发送的消息: ").strip()
            if text:
                method = input("发送方式 [1=回车 2=点击按钮]: ").strip()
                type_and_send(main_window, text, press_enter=(method != "2"))

        elif choice == "8":
            path = input("输入 EXE 完整路径: ").strip()
            try:
                app = connect_by_path(path)
                print(f"[✓] 已启动: {path}")
                windows = app.windows()
                if windows:
                    window_title = windows[0].window_text()
                    main_window = windows[0]
                    print(f"[✓] 主窗口: {window_title}")
            except Exception as e:
                print(f"[!] 启动失败: {e}")

        elif choice == "0":
            print("再见！")
            break
        else:
            print("[!] 无效选择")


# ============================================================
#  主入口
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 命令行模式: python exe_inspector.py "窗口标题"
        title = sys.argv[1]
        print(f"检测窗口: {title}")
        inspect_app(title)
    else:
        # 交互式模式
        interactive_menu()
