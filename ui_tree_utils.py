"""
UI 控件树工具库
提供：连接窗口、遍历控件树、搜索控件、导出结构 等通用能力

用法:
    from ui_tree_utils import UITree

    tree = UITree.connect("私信聚合 1.4.8")
    tree.dump(max_depth=6)
    tree.save_json("ui_tree.json")

    edits = tree.find(control_type="Edit")
    buttons = tree.find(control_type="Button", title="发送")
"""

import json
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ControlInfo:
    """控件信息快照"""
    type: str = ""
    title: str = ""
    auto_id: str = ""
    class_name: str = ""
    rect: tuple = (0, 0, 0, 0)
    children: list = field(default_factory=list)


class UITree:
    """
    UI 控件树操作工具

    创建方式:
        tree = UITree.connect("窗口标题")          # 连接已运行的窗口
        tree = UITree.launch(r"C:\\app.exe")       # 启动并连接
        tree = UITree.from_window(window_obj)       # 从 pywinauto window 对象
    """

    def __init__(self, window):
        self._win = window

    # ----------------------------------------------------------
    #  连接 / 启动
    # ----------------------------------------------------------

    @classmethod
    def connect(cls, title: str, timeout: int = 10):
        """通过窗口标题连接（支持部分匹配）"""
        from pywinauto import Desktop, Application

        # 精确匹配
        try:
            app = Application(backend="uia").connect(title=title)
            win = app.window(title=title)
            win.wait("exists visible", timeout=timeout)
            return cls(win)
        except Exception:
            pass

        # 模糊匹配
        desktop = Desktop(backend="uia")
        for w in desktop.windows():
            if title in w.window_text():
                app = Application(backend="uia").connect(title=w.window_text())
                win = app.window(title=w.window_text())
                win.wait("exists visible", timeout=timeout)
                return cls(win)

        raise RuntimeError(f"未找到窗口: {title}")

    @classmethod
    def launch(cls, exe_path: str, timeout: int = 10, wait: float = 3.0):
        """通过 EXE 路径启动并连接"""
        from pywinauto import Application

        app = Application(backend="uia").start(exe_path)
        time.sleep(wait)
        windows = app.windows()
        if not windows:
            raise RuntimeError(f"启动后未发现窗口: {exe_path}")
        win = windows[0]
        win.wait("exists visible", timeout=timeout)
        return cls(win)

    @classmethod
    def from_window(cls, window):
        """从已有的 pywinauto window 对象创建"""
        return cls(window)

    @classmethod
    def list_windows(cls):
        """列出系统所有可见窗口，返回 [(title, handle), ...]"""
        from pywinauto import Desktop
        desktop = Desktop(backend="uia")
        result = []
        for w in desktop.windows():
            title = w.window_text()
            if title.strip():
                result.append((title, w.handle))
        return result

    # ----------------------------------------------------------
    #  属性
    # ----------------------------------------------------------

    @property
    def window(self):
        """获取底层 pywinauto window 对象"""
        return self._win

    @property
    def title(self) -> str:
        return self._win.window_text()

    # ----------------------------------------------------------
    #  遍历控件树
    # ----------------------------------------------------------

    def walk(self, element=None, depth: int = 0, max_depth: int = 10):
        """
        递归遍历控件树，yield (depth, ControlInfo, raw_element)

        for depth, info, elem in tree.walk(max_depth=6):
            print(f"{'  '*depth}[{info.type}] {info.title}")
        """
        if element is None:
            element = self._win
        if depth > max_depth:
            return

        info = self._extract_info(element)
        yield depth, info, element

        try:
            for child in element.children():
                yield from self.walk(child, depth + 1, max_depth)
        except Exception:
            pass

    def dump(self, max_depth: int = 10, element=None) -> list[str]:
        """
        打印控件树，返回所有行（也可直接 print）
        """
        lines = []
        for depth, info, _ in self.walk(element=element, max_depth=max_depth):
            indent = "  " * depth
            line = (
                f"{indent}[{info.type}] "
                f'title="{info.title}" '
                f'auto_id="{info.auto_id}" '
                f'class="{info.class_name}" '
                f"rect={info.rect}"
            )
            lines.append(line)
            print(line)
        return lines

    # ----------------------------------------------------------
    #  搜索控件
    # ----------------------------------------------------------

    def find(
        self,
        control_type: Optional[str] = None,
        title: Optional[str] = None,
        auto_id: Optional[str] = None,
        class_name: Optional[str] = None,
        title_contains: Optional[str] = None,
    ) -> list:
        """
        搜索满足条件的控件，返回 pywinauto 控件列表

        参数:
            control_type:   控件类型 (Button, Edit, List, ListItem, Text, ...)
            title:          标题精确匹配
            auto_id:        automation_id 精确匹配
            class_name:     类名精确匹配
            title_contains: 标题包含指定文字（模糊匹配）

        用法:
            edits = tree.find(control_type="Edit")
            send_btns = tree.find(control_type="Button", title_contains="发送")
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
            controls = self._win.descendants(**criteria)
        except Exception:
            return []

        # 模糊标题过滤
        if title_contains:
            keyword = title_contains.lower()
            controls = [
                c for c in controls
                if keyword in (c.window_text() or "").lower()
            ]

        return controls

    def find_first(self, **kwargs):
        """搜索并返回第一个匹配的控件，没有则返回 None"""
        results = self.find(**kwargs)
        return results[0] if results else None

    def find_chat_controls(self) -> dict:
        """
        自动检测聊天相关控件

        返回:
            {
                "message_list": [...],   # 消息列表控件
                "input_box":    [...],   # 输入框
                "send_button":  [...],   # 发送按钮
            }
        """
        result = {"message_list": [], "input_box": [], "send_button": []}

        # 消息列表
        for ctype in ["List", "ListView", "ListBox", "TreeView", "DataGrid"]:
            result["message_list"].extend(self.find(control_type=ctype))

        # 输入框
        result["input_box"] = self.find(control_type="Edit")

        # 发送按钮（模糊匹配）
        for keyword in ["发送", "Send", "submit", "确定"]:
            btns = self.find(control_type="Button", title_contains=keyword)
            result["send_button"].extend(btns)

        # 去重
        for key in result:
            seen = set()
            unique = []
            for c in result[key]:
                cid = id(c)
                if cid not in seen:
                    seen.add(cid)
                    unique.append(c)
            result[key] = unique

        return result

    # ----------------------------------------------------------
    #  获取列表项
    # ----------------------------------------------------------

    def get_list_items(self, list_index: int = 0) -> list:
        """
        获取第 N 个列表控件的所有子项

        参数:
            list_index: 第几个列表控件（默认第一个）

        返回:
            [控件对象, ...]
        """
        lists = self.find(control_type="List")
        if not lists:
            lists = self.find(control_type="ListView")
        if not lists:
            lists = self.find(control_type="ListBox")

        if list_index >= len(lists):
            return []

        try:
            return lists[list_index].children()
        except Exception:
            return []

    # ----------------------------------------------------------
    #  导出
    # ----------------------------------------------------------

    def to_dict(self, element=None, depth: int = 0, max_depth: int = 8) -> Optional[dict]:
        """将控件树导出为嵌套字典"""
        if element is None:
            element = self._win
        if depth > max_depth:
            return None

        info = self._extract_info(element)
        node = {
            "type": info.type,
            "title": info.title,
            "auto_id": info.auto_id,
            "class_name": info.class_name,
            "rect": {
                "left": info.rect[0],
                "top": info.rect[1],
                "right": info.rect[2],
                "bottom": info.rect[3],
            },
            "children": [],
        }

        try:
            for child in element.children():
                child_node = self.to_dict(child, depth + 1, max_depth)
                if child_node:
                    node["children"].append(child_node)
        except Exception:
            pass

        return node

    def save_json(self, filepath: str, max_depth: int = 8):
        """导出控件树为 JSON 文件"""
        tree = self.to_dict(max_depth=max_depth)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)
        print(f"[✓] 已保存: {filepath}")

    def save_txt(self, filepath: str, max_depth: int = 10):
        """导出控件树为文本文件"""
        lines = []
        for depth, info, _ in self.walk(max_depth=max_depth):
            indent = "  " * depth
            line = (
                f"{indent}[{info.type}] "
                f'title="{info.title}" '
                f'auto_id="{info.auto_id}" '
                f'class="{info.class_name}" '
                f"rect={info.rect}"
            )
            lines.append(line)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"[✓] 已保存: {filepath}")

    # ----------------------------------------------------------
    #  内部方法
    # ----------------------------------------------------------

    @staticmethod
    def _extract_info(element) -> ControlInfo:
        """提取控件信息"""
        info = ControlInfo()
        try:
            info.type = element.element_info.control_type or "Unknown"
        except Exception:
            pass
        try:
            info.title = element.window_text() or ""
        except Exception:
            pass
        try:
            info.auto_id = element.element_info.automation_id or ""
        except Exception:
            pass
        try:
            info.class_name = element.element_info.class_name or ""
        except Exception:
            pass
        try:
            r = element.rectangle()
            info.rect = (r.left, r.top, r.right, r.bottom)
        except Exception:
            pass
        return info
