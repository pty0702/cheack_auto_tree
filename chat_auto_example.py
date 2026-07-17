"""
聊天应用自动化示例
使用 exe_inspector.py 的功能，演示完整的聊天自动化流程
"""

import time
from exe_inspector import (
    connect_by_title,
    connect_by_path,
    inspect_app,
    find_controls,
    find_chat_messages,
    click_message_by_index,
    type_and_send,
    save_tree_json,
)


def demo_full_flow():
    """完整演示：连接 → 检测 → 点击消息 → 发送"""

    # ============================
    # 第一步：连接到目标应用
    # ============================
    # 方式 A：通过窗口标题连接（应用已运行）
    WINDOW_TITLE = "你的应用窗口标题"  # ← 改成你的 EXE 窗口标题
    main_window = connect_by_title(WINDOW_TITLE)

    # 方式 B：通过 EXE 路径启动
    # app = connect_by_path(r"C:\path\to\your\app.exe")
    # main_window = app.window(title=WINDOW_TITLE)

    main_window.wait("exists visible", timeout=10)
    print(f"[✓] 已连接到: {WINDOW_TITLE}")

    # ============================
    # 第二步：检测 UI 结构
    # ============================
    print("\n--- 检测 UI 控件树 ---")
    dump_control_tree(main_window, max_depth=6)
    save_tree_json(WINDOW_TITLE, "chat_ui_tree.json")

    # ============================
    # 第三步：自动发现聊天控件
    # ============================
    print("\n--- 自动发现聊天相关控件 ---")
    chat_controls = find_chat_messages(main_window)

    print(f"消息列表: {len(chat_controls['message_list'])} 个")
    print(f"输入框:   {len(chat_controls['input_box'])} 个")
    print(f"发送按钮: {len(chat_controls['send_button'])} 个")

    # ============================
    # 第四步：点击某条消息
    # ============================
    print("\n--- 点击第 0 条消息 ---")
    click_message_by_index(main_window, msg_index=0)
    time.sleep(0.5)

    # ============================
    # 第五步：输入并发送消息
    # ============================
    print("\n--- 发送消息 ---")
    type_and_send(main_window, "你好，这是自动发送的消息！", press_enter=True)
    time.sleep(1)

    # 发送第二条
    type_and_send(main_window, "第二条自动消息 ✓", press_enter=True)


def demo_batch_send():
    """批量发送消息示例"""

    WINDOW_TITLE = "你的应用窗口标题"  # ← 改成你的窗口标题
    main_window = connect_by_title(WINDOW_TITLE)
    main_window.wait("exists visible", timeout=10)

    messages = [
        "消息 1：Hello!",
        "消息 2：这是批量发送测试",
        "消息 3：自动化真方便",
        "消息 4：最后一条",
    ]

    for i, msg in enumerate(messages):
        print(f"\n[{i+1}/{len(messages)}] 发送: {msg}")
        type_and_send(main_window, msg, press_enter=True)
        time.sleep(2)  # 间隔 2 秒，避免过快


def demo_click_specific_item():
    """点击指定控件示例"""

    WINDOW_TITLE = "你的应用窗口标题"
    main_window = connect_by_title(WINDOW_TITLE)

    # 示例：找到所有 Button 并点击第 3 个
    buttons = find_controls(main_window, control_type="Button")
    print(f"找到 {len(buttons)} 个按钮:")
    for i, btn in enumerate(buttons):
        print(f"  [{i}] {btn.window_text()}")

    if len(buttons) > 2:
        buttons[2].click_input()
        print("[✓] 已点击第 3 个按钮")


if __name__ == "__main__":
    # 选择要运行的演示
    print("请选择演示:")
    print("  1. 完整流程（检测 + 点击 + 发送）")
    print("  2. 批量发送消息")
    print("  3. 点击指定控件")

    choice = input("选择 [1/2/3]: ").strip()

    if choice == "1":
        demo_full_flow()
    elif choice == "2":
        demo_batch_send()
    elif choice == "3":
        demo_click_specific_item()
    else:
        print("运行完整流程演示...")
        demo_full_flow()
