# check_auto_tree

Windows EXE 应用 UI 控件树检测工具，基于 `pywinauto`。

## 安装

```bash
pip install pywinauto
```

## 快速使用

```python
from ui_tree_utils import UITree

# 连接窗口
tree = UITree.connect("你的窗口标题")

# 打印控件树
tree.dump(max_depth=6)

# 搜索控件
edits = tree.find(control_type="Edit")
btns = tree.find(control_type="Button", title_contains="发送")

# 自动检测聊天控件
chat = tree.find_chat_controls()
# chat["message_list"], chat["input_box"], chat["send_button"]

# 获取列表项
items = tree.get_list_items(list_index=0)
items[0].click_input()

# 导出
tree.save_json("ui_tree.json")
tree.save_txt("ui_tree.txt")
```

## API

| 方法 | 说明 |
|------|------|
| `UITree.connect(title)` | 通过窗口标题连接 |
| `UITree.launch(exe_path)` | 通过 EXE 路径启动 |
| `UITree.list_windows()` | 列出所有可见窗口 |
| `tree.dump(max_depth)` | 打印控件树 |
| `tree.find(control_type=, title=, auto_id=, class_name=, title_contains=)` | 搜索控件 |
| `tree.find_first(...)` | 搜索第一个匹配 |
| `tree.find_chat_controls()` | 自动检测聊天控件 |
| `tree.get_list_items(index)` | 获取列表子项 |
| `tree.save_json(path)` | 导出 JSON |
| `tree.save_txt(path)` | 导出文本 |
