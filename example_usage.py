"""
ui_tree_utils 使用示例
"""

from ui_tree_utils import UITree


# ============================================================
#  1. 列出所有窗口
# ============================================================
print("=== 所有窗口 ===")
for title, handle in UITree.list_windows():
    print(f"  {title}")


# ============================================================
#  2. 连接目标应用
# ============================================================
tree = UITree.connect("私信聚合 1.4.8")
# 或者通过路径启动:
# tree = UITree.launch(r"C:\path\to\app.exe")


# ============================================================
#  3. 打印控件树
# ============================================================
print("\n=== 控件树 ===")
tree.dump(max_depth=6)


# ============================================================
#  4. 搜索控件
# ============================================================
# 按类型搜索
edits = tree.find(control_type="Edit")
print(f"\n找到 {len(edits)} 个输入框")

# 模糊搜索按钮
send_btns = tree.find(control_type="Button", title_contains="发送")
print(f"找到 {len(send_btns)} 个发送按钮")

# 精确搜索
specific = tree.find(control_type="Button", title="确定")


# ============================================================
#  5. 自动检测聊天控件
# ============================================================
chat = tree.find_chat_controls()
print(f"\n消息列表: {len(chat['message_list'])} 个")
print(f"输入框:   {len(chat['input_box'])} 个")
print(f"发送按钮: {len(chat['send_button'])} 个")


# ============================================================
#  6. 获取列表项并点击
# ============================================================
items = tree.get_list_items(list_index=0)
print(f"\n列表项: {len(items)} 个")
for i, item in enumerate(items[:5]):
    print(f"  [{i}] {item.window_text()}")

if items:
    items[0].click_input()  # 点击第一条


# ============================================================
#  7. 操作输入框
# ============================================================
input_box = tree.find_first(control_type="Edit")
if input_box:
    input_box.click_input()
    input_box.set_edit_text("自动发送的消息")


# ============================================================
#  8. 导出
# ============================================================
tree.save_json("ui_tree.json", max_depth=8)
tree.save_txt("ui_tree.txt", max_depth=10)
