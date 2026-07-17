# check_auto_tree

Windows EXE 应用 UI 控件树检测工具，基于 `pywinauto` 封装，用于检测任意 Windows 程序的界面结构，搜索控件，实现自动化点击和输入。

适用场景：自己开发的桌面应用、合法合规的 UI 自动化测试。

---

## 环境要求

- **Python 3.8+**
- **Windows 系统**
- 安装 Python 时务必勾选 **Add Python to PATH**

下载地址：https://www.python.org/downloads/

## 安装依赖

```bash
pip install pywinauto
```

---

## 快速开始

### 第一步：查看系统中所有窗口

先确认目标应用已经打开，然后列出所有窗口找到它的标题：

```python
from ui_tree_utils import UITree

windows = UITree.list_windows()
for title, handle in windows:
    print(title)
```

输出示例：
```
私信聚合 1.4.8
微信
记事本
...
```

记下你要操作的窗口标题，后面要用。

---

### 第二步：连接到目标窗口

```python
# 方式一：通过窗口标题连接（应用已打开的情况）
tree = UITree.connect("私信聚合 1.4.8")

# 方式二：通过 EXE 路径启动（应用还没打开）
tree = UITree.launch(r"C:\Program Files\私信聚合\私信聚合.exe")
```

> **注意**：`connect` 支持模糊匹配，标题里包含关键字就行，比如写 `"私信聚合"` 也能连上。

---

### 第三步：扫描控件树（最重要的一步）

这一步会打印出应用界面的完整结构，每个按钮、输入框、列表都是一个控件节点：

```python
tree.dump(max_depth=6)
```

输出示例：
```
[Window] title="私信聚合 1.4.8" auto_id="" class="TXMainFrame" rect=(0,0,1200,800)
  [Pane] title="" auto_id="" class="CPanelUI" rect=(0,0,1200,800)
    [List] title="消息列表" auto_id="msg_list" class="CListUI" rect=(10,10,400,700)
      [ListItem] title="你好" auto_id="" class="CListElementUI" rect=(10,10,390,50)
      [ListItem] title="在吗" auto_id="" class="CListElementUI" rect=(10,55,390,95)
      [ListItem] title="消息3" auto_id="" class="CListElementUI" rect=(10,100,390,140)
    [Edit] title="" auto_id="input_box" class="CEditUI" rect=(10,710,350,750)
    [Button] title="发送" auto_id="send_btn" class="CButtonUI" rect=(360,710,400,750)
```

看这个输出你就能知道：
- 消息列表的控件类型是 `List`，auto_id 是 `msg_list`
- 输入框的控件类型是 `Edit`，auto_id 是 `input_box`
- 发送按钮的控件类型是 `Button`，标题是 `"发送"`

**也可以导出成文件，方便慢慢看：**

```python
tree.save_txt("控件树.txt")     # 文本格式，人类可读
tree.save_json("控件树.json")   # JSON格式，程序可处理
```

---

## 搜索控件

知道控件树结构后，就可以精确搜索目标控件了。

### 按类型搜索

```python
# 找所有输入框
edits = tree.find(control_type="Edit")
print(f"找到 {len(edits)} 个输入框")

# 找所有按钮
buttons = tree.find(control_type="Button")
for i, btn in enumerate(buttons):
    print(f"  [{i}] {btn.window_text()}")
```

### 按标题搜索

```python
# 精确匹配
btn = tree.find(control_type="Button", title="发送")

# 模糊匹配（标题里包含关键字就行）
btns = tree.find(control_type="Button", title_contains="发送")

# 按 auto_id 搜索（最稳定，推荐）
input_box = tree.find_first(control_type="Edit", auto_id="input_box")
```

### 按类名搜索

```python
panels = tree.find(class_name="CPanelUI")
```

### 只找第一个

```python
edit = tree.find_first(control_type="Edit")
if edit:
    print(f"输入框内容: {edit.window_text()}")
```

---

## 自动检测聊天控件

如果你的应用是聊天类软件，可以直接用这个方法自动找到消息列表、输入框、发送按钮：

```python
chat = tree.find_chat_controls()

print(f"消息列表: {len(chat['message_list'])} 个")
print(f"输入框:   {len(chat['input_box'])} 个")
print(f"发送按钮: {len(chat['send_button'])} 个")
```

---

## 自动化操作

### 点击列表中的某条消息

```python
# 获取第一个列表的所有子项
items = tree.get_list_items(list_index=0)

print(f"共 {len(items)} 条消息:")
for i, item in enumerate(items):
    print(f"  [{i}] {item.window_text()}")

# 点击第 0 条消息
items[0].click_input()

# 双击第 1 条消息
items[1].double_click_input()
```

### 在输入框中输入文字

```python
input_box = tree.find_first(control_type="Edit")
input_box.click_input()          # 先点击获取焦点
input_box.set_edit_text("你好")   # 输入文字
```

### 点击发送按钮

```python
send_btn = tree.find_first(control_type="Button", title_contains="发送")
send_btn.click_input()
```

### 完整示例：自动发送一条消息

```python
from ui_tree_utils import UITree
from pywinauto.keyboard import send_keys
import time

tree = UITree.connect("私信聚合 1.4.8")

# 找到输入框
input_box = tree.find_first(control_type="Edit")

# 点击输入框、输入文字
input_box.click_input()
time.sleep(0.3)
input_box.set_edit_text("自动发送的消息")
time.sleep(0.3)

# 按回车发送
send_keys("{ENTER}")
```

### 完整示例：批量发送消息

```python
from ui_tree_utils import UITree
from pywinauto.keyboard import send_keys
import time

tree = UITree.connect("私信聚合 1.4.8")
input_box = tree.find_first(control_type="Edit")

messages = ["第一条消息", "第二条消息", "第三条消息"]

for msg in messages:
    input_box.click_input()
    time.sleep(0.2)
    input_box.set_edit_text(msg)
    time.sleep(0.2)
    send_keys("{ENTER}")
    print(f"已发送: {msg}")
    time.sleep(2)  # 间隔2秒，避免太快
```

### 完整示例：点击消息列表后回复

```python
from ui_tree_utils import UITree
from pywinauto.keyboard import send_keys
import time

tree = UITree.connect("私信聚合 1.4.8")

# 获取消息列表
items = tree.get_list_items(list_index=0)

# 点击最新一条消息
if items:
    items[-1].click_input()
    time.sleep(0.5)

# 输入回复
input_box = tree.find_first(control_type="Edit")
input_box.click_input()
input_box.set_edit_text("收到，已处理")
send_keys("{ENTER}")
```

---

## 完整 API 参考

### 创建连接

| 方法 | 说明 | 示例 |
|------|------|------|
| `UITree.connect(title)` | 通过窗口标题连接，支持模糊匹配 | `UITree.connect("私信聚合")` |
| `UITree.launch(exe_path)` | 通过 EXE 路径启动并连接 | `UITree.launch(r"C:\app.exe")` |
| `UITree.from_window(win)` | 从 pywinauto 的 window 对象创建 | `UITree.from_window(my_win)` |
| `UITree.list_windows()` | 列出系统所有可见窗口 | 返回 `[(标题, 句柄), ...]` |

### 遍历控件树

| 方法 | 说明 |
|------|------|
| `tree.dump(max_depth=10)` | 打印控件树到终端，返回行列表 |
| `tree.walk(max_depth=10)` | 遍历控件树，yield `(depth, ControlInfo, element)` |
| `tree.title` | 当前窗口标题 |

### 搜索控件

| 方法 | 说明 |
|------|------|
| `tree.find(control_type="Edit")` | 按类型搜索，返回列表 |
| `tree.find(title="发送")` | 按标题精确匹配 |
| `tree.find(title_contains="发送")` | 按标题模糊匹配 |
| `tree.find(auto_id="btn_ok")` | 按 automation_id 搜索 |
| `tree.find(class_name="CButtonUI")` | 按类名搜索 |
| `tree.find_first(...)` | 同 find，但只返回第一个结果 |

可组合使用：`tree.find(control_type="Button", title_contains="发送")`

### 聊天专用

| 方法 | 说明 |
|------|------|
| `tree.find_chat_controls()` | 自动检测消息列表、输入框、发送按钮，返回 dict |
| `tree.get_list_items(index=0)` | 获取第 N 个列表的所有子项 |

### 导出

| 方法 | 说明 |
|------|------|
| `tree.save_json("out.json", max_depth=8)` | 导出控件树为 JSON 文件 |
| `tree.save_txt("out.txt", max_depth=10)` | 导出控件树为文本文件 |
| `tree.to_dict(max_depth=8)` | 导出为 Python 字典（不写文件） |

---

## 常见控件类型速查

| 类型 | 说明 | 常见用途 |
|------|------|----------|
| `Window` | 顶层窗口 | 应用主窗口 |
| `Pane` | 面板/容器 | 布局容器 |
| `Button` | 按钮 | 发送、确定、取消 |
| `Edit` | 输入框 | 文本输入 |
| `Text` | 静态文本 | 标签、提示文字 |
| `List` | 列表 | 消息列表、联系人列表 |
| `ListItem` | 列表项 | 单条消息、单个联系人 |
| `ComboBox` | 下拉框 | 选项选择 |
| `CheckBox` | 复选框 | 多选 |
| `Tab` | 标签页 | 页面切换 |
| `TreeView` | 树形列表 | 文件目录、分组 |
| `DataGrid` | 数据表格 | 表格数据 |

---

## 常见问题

### Q: 找不到窗口怎么办？

确认应用已经打开，然后用 `UITree.list_windows()` 看看实际的窗口标题是什么。有些应用标题带版本号或动态内容。

### Q: dump 输出太多/太少？

调整 `max_depth` 参数，数字越大看得越深，一般 6~8 就够了。

### Q: find 搜不到控件？

1. 先 `dump` 看看控件树里到底有没有这个控件
2. 试试放宽条件，比如只用 `control_type` 搜索
3. 有些控件可能是自绘的（custom draw），pywinauto 识别不了，这种情况需要用 `pyautogui` 按坐标点击

### Q: 中文输入不了？

用 `set_edit_text()` 方法而不是键盘输入，它直接设置控件文本，不走输入法。

### Q: 操作太快导致失败？

在操作之间加 `time.sleep(0.3~1.0)` 等一下。
