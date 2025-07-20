import itertools
import argparse
import json
import os
import random
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QMessageBox, QLineEdit, 
                            QDialog, QFormLayout, QSpinBox, QDialogButtonBox, QInputDialog,
                            QListWidget, QListWidgetItem, QFileDialog, QComboBox, QRadioButton,
                            QButtonGroup)
from PyQt5.QtCore import Qt, QDateTime, QSize, QRect, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush, QImage, QPainter, QPen

def is_valid(board, row, col, num, symbols):
    """检查在指定位置放置指定数字/符号是否有效"""
    n = len(board)
    
    # 检查行
    for i in range(n):
        if board[row][i] == num:
            return False
    
    # 检查列
    for i in range(n):
        if board[i][col] == num:
            return False
    
    # 检查小九宫格
    box_size = int(n ** 0.5)
    box_row = (row // box_size) * box_size
    box_col = (col // box_size) * box_size
    
    for i in range(box_size):
        for j in range(box_size):
            if board[box_row + i][box_col + j] == num:
                return False
    
    return True

def solve_sudoku(board, symbols):
    """使用回溯法求解数独"""
    n = len(board)
    
    # 找到第一个空格
    for row in range(n):
        for col in range(n):
            if board[row][col] == '':
                # 尝试填充每个可能的数字/符号
                for num in symbols:
                    if is_valid(board, row, col, num, symbols):
                        board[row][col] = num
                        
                        # 递归求解剩余的数独
                        if solve_sudoku(board, symbols):
                            return True
                        
                        # 如果填充当前数字/符号后无法求解，则回溯
                        board[row][col] = ''
                
                # 如果所有数字/符号都无法填充，则返回False
                return False
    
    # 如果没有找到空格，则数独已解
    return True

class ChallengeDialog(QDialog):
    """挑战模式对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("挑战模式")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # 难度选择
        difficulty_group = QButtonGroup(self)
        difficulty_layout = QHBoxLayout()
        difficulty_label = QLabel("难度:")
        difficulty_layout.addWidget(difficulty_label)
        
        difficulties = ["简单", "中等", "困难"]
        for i, diff in enumerate(difficulties):
            radio = QRadioButton(diff)
            if i == 0:  # 默认选择简单
                radio.setChecked(True)
            difficulty_group.addButton(radio, i)
            difficulty_layout.addWidget(radio)
        
        layout.addLayout(difficulty_layout)
        self.difficulty_group = difficulty_group
        
        # 大小选择
        size_layout = QHBoxLayout()
        size_label = QLabel("数独大小:")
        self.size_spin = QSpinBox()
        self.size_spin.setRange(2, 5)
        self.size_spin.setValue(3)
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_spin)
        layout.addLayout(size_layout)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_settings(self):
        """获取设置"""
        difficulty = self.difficulty_group.checkedButton().text()
        size = self.size_spin.value()
        return difficulty, size

class ChallengeMode(QMainWindow):
    """挑战模式窗口"""
    # 定义难度级别对应的空格率
    difficulties = {
        "简单": (0.4, 0.5),  # 40-50%空格
        "中等": (0.5, 0.6),  # 50-60%空格
        "困难": (0.6, 0.7)   # 60-70%空格
    }
    
    def __init__(self, difficulty, size, parent=None):
        super().__init__(parent)
        self.difficulty = difficulty
        self.box_size = size
        self.n = size ** 2
        self.symbols = list("123456789"[:self.n])
        self.solution = None
        self.start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        self.setWindowTitle(f"数独挑战 - {difficulty}难度")
        self.resize(800, 600)
        self.init_ui()
        self.generate_puzzle()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加计时器标签
        self.time_label = QLabel("用时: 00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont("Arial", 14))
        layout.addWidget(self.time_label)
        
        # 添加网格
        self.grid_frame = QWidget()
        self.grid_layout = QGridLayout(self.grid_frame)
        self.grid_layout.setSpacing(0)
        layout.addWidget(self.grid_frame)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        
        check_button = QPushButton("检查答案")
        check_button.clicked.connect(self.check_solution)
        button_layout.addWidget(check_button)
        
        show_solution_button = QPushButton("显示答案")
        show_solution_button.clicked.connect(self.show_solution)
        button_layout.addWidget(show_solution_button)
        
        new_puzzle_button = QPushButton("新题目")
        new_puzzle_button.clicked.connect(self.generate_puzzle)
        button_layout.addWidget(new_puzzle_button)
        
        layout.addLayout(button_layout)
        
        # 创建输入格子
        self.entries = [[None for _ in range(self.n)] for _ in range(self.n)]
        for i in range(self.n):
            for j in range(self.n):
                entry = QLineEdit()
                entry.setAlignment(Qt.AlignCenter)
                entry.setFont(QFont("Arial", 16))
                
                borders = []
                if i % self.box_size == 0:
                    borders.append("border-top: 3px solid #000")
                else:
                    borders.append("border-top: 1px solid #888")
                if j % self.box_size == 0:
                    borders.append("border-left: 3px solid #000")
                else:
                    borders.append("border-left: 1px solid #888")
                if (i + 1) % self.box_size == 0:
                    borders.append("border-bottom: 3px solid #000")
                else:
                    borders.append("border-bottom: 1px solid #888")
                if (j + 1) % self.box_size == 0:
                    borders.append("border-right: 3px solid #000")
                else:
                    borders.append("border-right: 1px solid #888")
                
                if (i // self.box_size + j // self.box_size) % 2 == 0:
                    borders.append("background-color: #f8f8f8")
                
                entry.setStyleSheet("; ".join(borders))
                entry.setFixedSize(400 // self.n, 400 // self.n)
                entry.textChanged.connect(self.validate_input)
                self.entries[i][j] = entry
                self.grid_layout.addWidget(entry, i, j)
    
    def generate_puzzle(self):
        """生成新的数独题目"""
        # 创建一个完整的解决方案
        board = [['' for _ in range(self.n)] for _ in range(self.n)]
        solve_sudoku(board, self.symbols)  # 生成完整解
        self.solution = [row.copy() for row in board]
        
        # 根据难度决定要移除多少数字
        removal_rate = random.uniform(*self.difficulties[self.difficulty])
        cells_to_remove = int(self.n * self.n * removal_rate)
        
        # 随机移除数字
        positions = [(i, j) for i in range(self.n) for j in range(self.n)]
        random.shuffle(positions)
        positions = positions[:cells_to_remove]
        
        # 创建题目
        puzzle = [row.copy() for row in board]
        for i, j in positions:
            puzzle[i][j] = ''
        
        # 显示题目
        for i in range(self.n):
            for j in range(self.n):
                entry = self.entries[i][j]
                value = puzzle[i][j]
                entry.setText(value)
                if value:  # 题目中给出的数字
                    entry.setReadOnly(True)
                    style = entry.styleSheet()
                    if 'color: ' in style:
                        style = '; '.join([s for s in style.split('; ') if not s.startswith('color:')])
                    style += '; color: #FF0000'  # 题目用红色显示
                    entry.setStyleSheet(style)
                else:
                    entry.setReadOnly(False)
        
        # 重置并启动计时器
        self.start_time = time.time()
        self.timer.start(1000)  # 每秒更新一次
        
        self.statusBar().showMessage(f"已生成{self.n}x{self.n}的数独题目，难度: {self.difficulty}")
    
    def validate_input(self):
        """验证输入"""
        sender = self.sender()
        if sender:
            text = sender.text()
            if text and text not in self.symbols:
                sender.setText('')
            elif text:
                style = sender.styleSheet()
                if 'color: ' in style:
                    style = '; '.join([s for s in style.split('; ') if not s.startswith('color:')])
                style += '; color: #FFA500'  # 用户输入用橙色显示
                sender.setStyleSheet(style)
    
    def get_current_state(self):
        """获取当前状态"""
        state = [['' for _ in range(self.n)] for _ in range(self.n)]
        for i in range(self.n):
            for j in range(self.n):
                state[i][j] = self.entries[i][j].text()
        return state
    
    def check_solution(self):
        """检查答案"""
        current = self.get_current_state()
        if all(current[i][j] == self.solution[i][j] 
              for i in range(self.n) 
              for j in range(self.n)):
            elapsed = time.time() - self.start_time
            minutes, seconds = divmod(int(elapsed), 60)
            self.timer.stop()
            
            # 获取题目状态（只包含红色数字）和用户答案状态
            puzzle_state = [['' for _ in range(self.n)] for _ in range(self.n)]
            user_answer_state = [['' for _ in range(self.n)] for _ in range(self.n)]
            for i in range(self.n):
                for j in range(self.n):
                    entry = self.entries[i][j]
                    value = entry.text()
                    style = entry.styleSheet()
                    if 'color: #FF0000' in style:  # 题目（红色）
                        puzzle_state[i][j] = value
                    elif 'color: #FFA500' in style:  # 用户答案（橙色）
                        user_answer_state[i][j] = value
            
            # 保存到历史记录
            timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            history_entry = {
                "puzzle": puzzle_state,  # 原始题目
                "input": user_answer_state,  # 用户答案
                "result": self.solution,  # 正确答案
                "symbols": self.symbols,
                "size": self.box_size,
                "mode": "挑战模式",
                "difficulty": self.difficulty,
                "time": f"{minutes:02d}:{seconds:02d}"
            }
            # 获取主窗口并保存历史记录
            main_window = self.parent()
            if main_window and isinstance(main_window, SudokuSolverApp):
                main_window.history.append((timestamp, history_entry))
                main_window.save_history()
            
            QMessageBox.information(self, "恭喜", 
                                  f"答案正确！\n用时: {minutes:02d}:{seconds:02d}")
        else:
            QMessageBox.warning(self, "提示", "答案不正确，请继续尝试")
    
    def show_solution(self):
        """显示答案"""
        if QMessageBox.question(self, "确认", "确定要查看答案吗？") == QMessageBox.Yes:
            self.timer.stop()
            for i in range(self.n):
                for j in range(self.n):
                    entry = self.entries[i][j]
                    if not entry.isReadOnly():  # 只填写用户未填写的部分
                        entry.setText(self.solution[i][j])
                        style = entry.styleSheet()
                        if 'color: ' in style:
                            style = '; '.join([s for s in style.split('; ') if not s.startswith('color:')])
                        style += '; color: #008000'  # 答案用绿色显示
                        entry.setStyleSheet(style)
    
    def update_timer(self):
        """更新计时器显示"""
        elapsed = time.time() - self.start_time
        minutes, seconds = divmod(int(elapsed), 60)
        self.time_label.setText(f"用时: {minutes:02d}:{seconds:02d}")

class HistoryDialog(QDialog):
    """历史记录对话框"""
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle("求解历史记录")
        self.resize(800, 600)
        self.history = history
        self.parent = parent
        
        layout = QVBoxLayout(self)
        
        # 创建顶部按钮布局
        button_layout = QHBoxLayout()
        
        # 添加加载按钮
        load_button = QPushButton("加载选中记录")
        load_button.clicked.connect(self.load_selected)
        button_layout.addWidget(load_button)
        
        # 添加导出按钮
        export_button = QPushButton("导出选中记录")
        export_button.clicked.connect(self.export_selected)
        button_layout.addWidget(export_button)
        
        # 添加关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # 创建列表控件
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        # 设置等宽字体以确保对齐
        self.list_widget.setFont(QFont("Courier New", 12))
        layout.addWidget(self.list_widget)
        
        # 倒序添加历史记录
        for timestamp, data in reversed(history):
            # 添加时间戳组（可选中的主项）
            mode = data.get("mode", "普通模式")
            header = f"求解时间: {timestamp}"
            if mode == "挑战模式":
                difficulty = data.get("difficulty", "未知")
                solve_time = data.get("time", "未记录")
                header += f" [挑战模式 - {difficulty} - 用时: {solve_time}]"
            
            timestamp_item = QListWidgetItem(header)
            timestamp_item.setData(Qt.UserRole, (timestamp, data))  # 存储完整数据
            self.list_widget.addItem(timestamp_item)
            
            n = len(data["input"])  # 获取数独大小
            box_size = int(n ** 0.5)
            
            # 添加输入状态标题和内容
            if data.get("mode") == "挑战模式":
                # 显示题目
                input_title = QListWidgetItem("┌─题目" + "─" * (4 * n + 2) + "┐")
                input_title.setForeground(QBrush(QColor("#FF0000")))
                input_title.setFlags(input_title.flags() & ~Qt.ItemIsSelectable)
                self.list_widget.addItem(input_title)
                
                # 添加题目状态（带有网格线）
                puzzle = data.get("puzzle", [['' for _ in range(n)] for _ in range(n)])
                for i, row in enumerate(puzzle):
                    # 构建行字符串，包括垂直分隔线
                    row_str = "│ "
                    for j, cell in enumerate(row):
                        row_str += f" {cell if cell else '·'} "
                        if (j + 1) % box_size == 0 and j < n - 1:
                            row_str += "│ "
                        elif j < n - 1:
                            row_str += " "
                    row_str += " │"
                    
                    row_item = QListWidgetItem(row_str)
                    row_item.setForeground(QBrush(QColor("#FF0000")))  # 题目用红色显示
                    row_item.setFlags(row_item.flags() & ~Qt.ItemIsSelectable)
                    self.list_widget.addItem(row_item)
                    
                    if (i + 1) % box_size == 0 and i < n - 1:
                        separator = QListWidgetItem("├" + "─" * (4 * n + 2) + "┤")
                        separator.setFlags(separator.flags() & ~Qt.ItemIsSelectable)
                        self.list_widget.addItem(separator)
                
                # 显示用户答案
                answer_title = QListWidgetItem("┌─用户答案" + "─" * (4 * n) + "┐")
                answer_title.setForeground(QBrush(QColor("#FFA500")))
                answer_title.setFlags(answer_title.flags() & ~Qt.ItemIsSelectable)
                self.list_widget.addItem(answer_title)
            else:
                # 普通模式下的输入状态显示
                input_title = QListWidgetItem("┌─输入状态" + "─" * (4 * n) + "┐")
                input_title.setForeground(QBrush(QColor("#FF0000")))
                input_title.setFlags(input_title.flags() & ~Qt.ItemIsSelectable)
                self.list_widget.addItem(input_title)
            
            # 添加输入状态（带有网格线）
            for i, row in enumerate(data["input"]):
                # 构建行字符串，包括垂直分隔线
                row_str = "│ "
                for j, cell in enumerate(row):
                    # 添加单元格内容
                    row_str += f" {cell if cell else '·'} "
                    # 添加垂直分隔线
                    if (j + 1) % box_size == 0 and j < n - 1:
                        row_str += "│ "
                    elif j < n - 1:
                        row_str += " "
                row_str += " │"
                
                row_item = QListWidgetItem(row_str)
                # 根据模式选择颜色
                if data.get("mode") == "挑战模式":
                    row_item.setForeground(QBrush(QColor("#FFA500")))  # 用户答案用橙色显示
                else:
                    row_item.setForeground(QBrush(QColor("#FF0000")))  # 普通模式用红色显示
                row_item.setFlags(row_item.flags() & ~Qt.ItemIsSelectable)
                self.list_widget.addItem(row_item)
                
                # 在每个小九宫格的底部添加水平分隔线
                if (i + 1) % box_size == 0 and i < n - 1:
                    separator = QListWidgetItem("├" + "─" * (4 * n + 2) + "┤")
                    separator.setFlags(separator.flags() & ~Qt.ItemIsSelectable)
                    self.list_widget.addItem(separator)
            
            # 添加输入状态的底边框
            bottom_border = QListWidgetItem("└" + "─" * (4 * n + 2) + "┘")
            bottom_border.setFlags(bottom_border.flags() & ~Qt.ItemIsSelectable)
            self.list_widget.addItem(bottom_border)
            
            # 添加箭头指示求解过程
            arrow = QListWidgetItem("        ↓ 求解结果")
            arrow.setForeground(QBrush(QColor("#008000")))
            arrow.setFlags(arrow.flags() & ~Qt.ItemIsSelectable)
            self.list_widget.addItem(arrow)
            
            # 添加求解结果标题
            result_title = QListWidgetItem("┌─求解结果" + "─" * (4 * n) + "┐")
            result_title.setForeground(QBrush(QColor("#008000")))
            result_title.setFlags(result_title.flags() & ~Qt.ItemIsSelectable)
            self.list_widget.addItem(result_title)
            
            # 添加求解结果（带有网格线）
            for i, row in enumerate(data["result"]):
                # 构建行字符串，包括垂直分隔线
                row_str = "│ "
                # 确定这一行是否所有数字都是解出的（用于决定边框颜色）
                is_solved_row = all(not data["input"][i][j] for j in range(n))
                
                for j, cell in enumerate(row):
                    # 添加单元格内容
                    row_str += f" {cell} "
                    # 添加垂直分隔线
                    if (j + 1) % box_size == 0 and j < n - 1:
                        row_str += "│ "
                    elif j < n - 1:
                        row_str += " "
                row_str += " │"
                
                row_item = QListWidgetItem(row_str)
                # 使用绿色显示解出的行，包括边框
                row_item.setForeground(QBrush(QColor("#008000")))
                row_item.setFlags(row_item.flags() & ~Qt.ItemIsSelectable)
                self.list_widget.addItem(row_item)
                
                # 在每个小九宫格的底部添加水平分隔线
                if (i + 1) % box_size == 0 and i < n - 1:
                    separator = QListWidgetItem("├" + "─" * (4 * n + 2) + "┤")
                    separator.setFlags(separator.flags() & ~Qt.ItemIsSelectable)
                    self.list_widget.addItem(separator)
            
            # 添加求解结果的底边框
            bottom_border = QListWidgetItem("└" + "─" * (4 * n + 2) + "┘")
            bottom_border.setFlags(bottom_border.flags() & ~Qt.ItemIsSelectable)
            self.list_widget.addItem(bottom_border)
            
            # 添加空行作为记录之间的分隔
            self.list_widget.addItem("")
    
    def export_selected(self):
        """导出选中的历史记录"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要导出的记录")
            return
            
        # 创建导出选项对话框
        export_dialog = QDialog(self)
        export_dialog.setWindowTitle("导出选项")
        export_dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(export_dialog)
        
        # 添加格式选择
        format_layout = QHBoxLayout()
        format_label = QLabel("导出格式:")
        format_combo = QComboBox()
        format_combo.addItems(["文本文件 (*.txt)", "PNG图片 (*.png)"])
        format_layout.addWidget(format_label)
        format_layout.addWidget(format_combo)
        layout.addLayout(format_layout)
        
        # 添加按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(export_dialog.accept)
        button_box.rejected.connect(export_dialog.reject)
        layout.addWidget(button_box)
        
        if export_dialog.exec_() != QDialog.Accepted:
            return
        
        # 获取选中项的数据
        item = selected_items[0]
        timestamp, data = item.data(Qt.UserRole)
        
        # 根据选择的格式确定文件类型和扩展名
        is_image = format_combo.currentIndex() == 1
        ext = ".png" if is_image else ".txt"
        file_filter = "PNG图片 (*.png)" if is_image else "文本文件 (*.txt)"
        default_name = f"数独记录_{timestamp.replace(':', '-')}{ext}"
        
        # 弹出文件保存对话框
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "保存文件",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), default_name),
            file_filter
        )
        
        if not filepath:
            return
            
        try:
            n = len(data["input"])
            box_size = int(n ** 0.5)
            
            if filepath.lower().endswith('.png'):
                # 创建图片并设置大小
                width = 800
                height = 1000
                image = QImage(width, height, QImage.Format_RGB32)
                image.fill(Qt.white)
                
                painter = QPainter(image)
                painter.setFont(QFont("Courier New", 12))
                
                # 写入标题信息
                header_text = f"求解时间: {timestamp}"
                if data.get("mode") == "挑战模式":
                    difficulty = data.get("difficulty", "未知")
                    solve_time = data.get("time", "未记录")
                    header_text += f"\n模式: 挑战模式 - {difficulty}"
                    header_text += f"\n用时: {solve_time}"
                
                # 绘制多行标题
                y = 30
                for line in header_text.split('\n'):
                    painter.drawText(20, y, line)
                    y += 20  # 每行文字间隔
                
                y = 80  # 当前绘制位置的y坐标
                cell_size = min(40, (width - 40) // (n + 2))  # 单元格大小
                grid_width = cell_size * n  # 网格总宽度
                x_offset = (width - grid_width) // 2  # 水平居中偏移
                
                # 绘制函数
                def draw_grid(data, title, y_pos, text_color):
                    nonlocal y
                    # 绘制标题
                    painter.setPen(text_color)
                    painter.drawText(20, y_pos, title)
                    y_pos += 30
                    
                    # 绘制网格
                    for i in range(n + 1):
                        pen_width = 2 if i % box_size == 0 else 1
                        painter.setPen(QPen(Qt.black, pen_width))
                        # 绘制水平线
                        painter.drawLine(x_offset, y_pos + i * cell_size,
                                      x_offset + n * cell_size, y_pos + i * cell_size)
                        # 绘制垂直线
                        painter.drawLine(x_offset + i * cell_size, y_pos,
                                      x_offset + i * cell_size, y_pos + n * cell_size)
                    
                    # 填充数字
                    painter.setFont(QFont("Arial", cell_size // 2))
                    for i in range(n):
                        for j in range(n):
                            value = data[i][j] if data[i][j] else '·'
                            painter.setPen(text_color)
                            rect = QRect(x_offset + j * cell_size, y_pos + i * cell_size,
                                       cell_size, cell_size)
                            painter.drawText(rect, Qt.AlignCenter, value)
                    
                    return y_pos + n * cell_size + 50
                
                # 绘制输入状态
                y = draw_grid(data["input"], "输入状态:", y, QColor("#FF0000"))
                # 绘制箭头
                painter.setPen(QColor("#008000"))
                painter.drawText(width//2 - 50, y - 30, "↓ 求解结果")
                # 绘制求解结果
                y = draw_grid(data["result"], "求解结果:", y, QColor("#008000"))
                
                painter.end()
                # 保存图片
                image.save(filepath)
                
            else:
                # 导出为文本文件
                with open(filepath, 'w', encoding='utf-8') as f:
                    # 写入标题信息
                    f.write(f"求解时间: {timestamp}\n")
                    if data.get("mode") == "挑战模式":
                        difficulty = data.get("difficulty", "未知")
                        solve_time = data.get("time", "未记录")
                        f.write(f"模式: 挑战模式 - {difficulty}\n")
                        f.write(f"用时: {solve_time}\n")
                    f.write("\n")
                    
                    # 写入输入状态
                    f.write("输入状态:\n")
                    f.write("┌" + "─" * (4 * n + 2) + "┐\n")
                    for i, row in enumerate(data["input"]):
                        # 写入数据行
                        row_str = "│ "
                        for j, cell in enumerate(row):
                            row_str += f" {cell if cell else '·'} "
                            if (j + 1) % box_size == 0 and j < n - 1:
                                row_str += "│ "
                            elif j < n - 1:
                                row_str += " "
                        row_str += " │\n"
                        f.write(row_str)
                        
                        # 写入分隔线
                        if (i + 1) % box_size == 0 and i < n - 1:
                            f.write("├" + "─" * (4 * n + 2) + "┤\n")
                    f.write("└" + "─" * (4 * n + 2) + "┘\n\n")
                    
                    # 写入求解结果
                    f.write("求解结果:\n")
                    f.write("┌" + "─" * (4 * n + 2) + "┐\n")
                    for i, row in enumerate(data["result"]):
                        # 写入数据行
                        row_str = "│ "
                        for j, cell in enumerate(row):
                            row_str += f" {cell} "
                            if (j + 1) % box_size == 0 and j < n - 1:
                                row_str += "│ "
                            elif j < n - 1:
                                row_str += " "
                        row_str += " │\n"
                        f.write(row_str)
                        
                        # 写入分隔线
                        if (i + 1) % box_size == 0 and i < n - 1:
                            f.write("├" + "─" * (4 * n + 2) + "┤\n")
                    f.write("└" + "─" * (4 * n + 2) + "┘\n")
            
            QMessageBox.information(self, "成功", f"历史记录已导出到：\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")
    
    def load_selected(self):
        """加载选中的历史记录到主窗口"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要加载的记录")
            return
        
        # 获取选中项的数据
        item = selected_items[0]
        timestamp, data = item.data(Qt.UserRole)
        
        # 将选中的数独加载到主窗口
        if isinstance(self.parent, SudokuSolverApp):
            # 更新棋盘大小
            box_size = data.get("size", int(len(data["input"]) ** 0.5))
            if self.parent.box_size != box_size:
                self.parent.box_size = box_size
                self.parent.n = box_size ** 2
                self.parent.new_sudoku()  # 重新创建网格
            
            # 设置符号
            symbols = data.get("symbols", None)
            if not symbols:
                symbols = set()
                for row in data["result"]:
                    symbols.update(row)
                symbols = sorted(list(symbols))
            self.parent.symbols = symbols
            
            # 加载结果状态
            self.parent.board = [row.copy() for row in data["result"]]
            self.parent.update_entries_from_board(input_state=data["input"])
            
            self.accept()  # 关闭对话框
            self.parent.statusBar().showMessage(f"已加载 {timestamp} 的记录")

class SudokuSolverApp(QMainWindow):
    """数独求解器的GUI界面"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("基于Python的简易数独学习软件")
        self.resize(800, 600)
        
        self.board = None
        self.entries = None
        self.symbols = None
        self.box_size = 3  # 默认3x3小九宫格
        self.n = self.box_size ** 2
        self.history = []  # 存储历史记录
        self.last_input = None  # 存储上次求解时的输入状态
        
        # 加载历史记录
        self.history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sudoku_history.json")
        self.load_history()
        
        self.init_ui()
        
    def init_ui(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建工具栏
        toolbar_layout = QHBoxLayout()
        
        solve_button = QPushButton("求解")
        solve_button.clicked.connect(self.solve)
        toolbar_layout.addWidget(solve_button)
        
        clear_button = QPushButton("清空")
        clear_button.clicked.connect(self.clear)
        toolbar_layout.addWidget(clear_button)
        
        new_button = QPushButton("新建")
        new_button.clicked.connect(self.new_sudoku)
        toolbar_layout.addWidget(new_button)
        
        history_button = QPushButton("历史记录")
        history_button.clicked.connect(self.show_history)
        toolbar_layout.addWidget(history_button)
        
        challenge_button = QPushButton("挑战模式")
        challenge_button.clicked.connect(self.start_challenge)
        toolbar_layout.addWidget(challenge_button)
        
        main_layout.addLayout(toolbar_layout)
        
        # 创建数独网格区域
        self.grid_frame = QWidget()
        self.grid_layout = QGridLayout(self.grid_frame)
        self.grid_layout.setSpacing(0)
        
        main_layout.addWidget(self.grid_frame, stretch=1)
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
        # 默认创建一个9x9数独
        self.new_sudoku()
    
    def new_sudoku(self):
        # 清除当前网格
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # 获取用户输入的数独大小
        size, ok = QInputDialog.getInt(self, "数独大小", "请输入小九宫格的大小（2～5）:", 
                                      self.box_size, 2, 5, 1)
        if not ok:
            return
            
        self.box_size = size
        self.n = self.box_size ** 2
        
        # 获取用户输入的符号
        symbols, ok = QInputDialog.getText(self, "符号", 
                                         f"请输入{self.n}个符号用于填充数独 (例如: 123456789 或 ABCDEFGHI):",
                                         text="123456789"[:self.n])
        if not ok or len(symbols) != self.n:
            QMessageBox.critical(self, "错误", f"符号数量必须等于{self.n}")
            return
            
        self.symbols = list(symbols)
        
        # 创建空的数独棋盘
        self.board = [['' for _ in range(self.n)] for _ in range(self.n)]
        self.entries = [[None for _ in range(self.n)] for _ in range(self.n)]
        # 重置上次求解的输入状态
        self.last_input = None
        
        # 创建数独网格
        for i in range(self.n):
            for j in range(self.n):
                # 确定边框样式
                entry = QLineEdit()
                entry.setAlignment(Qt.AlignCenter)
                entry.setFont(QFont("Arial", 16))
                
                # 设置边框样式和背景色
                borders = []
                if i % self.box_size == 0:
                    borders.append("border-top: 3px solid #000")
                else:
                    borders.append("border-top: 1px solid #888")
                if j % self.box_size == 0:
                    borders.append("border-left: 3px solid #000")
                else:
                    borders.append("border-left: 1px solid #888")
                if (i + 1) % self.box_size == 0:
                    borders.append("border-bottom: 3px solid #000")
                else:
                    borders.append("border-bottom: 1px solid #888")
                if (j + 1) % self.box_size == 0:
                    borders.append("border-right: 3px solid #000")
                else:
                    borders.append("border-right: 1px solid #888")
                
                # 设置交替背景色以增加可读性
                if (i // self.box_size + j // self.box_size) % 2 == 0:
                    borders.append("background-color: #f8f8f8")
                
                entry.setStyleSheet("; ".join(borders))
                
                # 设置固定大小
                entry.setFixedSize(400 // self.n, 400 // self.n)
                
                # 存储entry引用
                self.entries[i][j] = entry
                
                # 添加到网格布局
                self.grid_layout.addWidget(entry, i, j)
                
                # 为输入框添加验证
                entry.textChanged.connect(self.validate_input)
        
        self.statusBar().showMessage(f"创建了一个{self.n}x{self.n}的数独，使用符号: {''.join(self.symbols)}")
    
    def validate_input(self):
        """验证输入是否为允许的符号"""
        sender = self.sender()
        if sender:
            text = sender.text()
            if text and text not in self.symbols:
                sender.setText('')
            else:
                # 设置用户输入的文字为红色
                if text:
                    current_style = sender.styleSheet()
                    if 'color: ' in current_style:
                        # 保持现有样式，只更新颜色
                        new_style = '; '.join([s for s in current_style.split('; ') if not s.startswith('color:')])
                        new_style += '; color: #FF0000'
                    else:
                        new_style = current_style + '; color: #FF0000'
                    sender.setStyleSheet(new_style)
                # 更新原始输入状态
                self.get_original_input()
    
    def get_original_input(self):
        """获取用户的原始输入（红色数字）"""
        original_input = [['' for _ in range(self.n)] for _ in range(self.n)]
        for i in range(self.n):
            for j in range(self.n):
                entry = self.entries[i][j]
                # 检查是否是用户输入（红色文字）
                style = entry.styleSheet()
                if 'color: #FF0000' in style:
                    value = entry.text()
                    original_input[i][j] = value if value in self.symbols else ''
        self.current_input = original_input
        return original_input

    def get_board_from_entries(self):
        """从输入框获取数独棋盘"""
        for i in range(self.n):
            for j in range(self.n):
                value = self.entries[i][j].text()
                self.board[i][j] = value if value in self.symbols else ''
    
    def update_entries_from_board(self, input_state=None):
        """用数独棋盘更新输入框
        Args:
            input_state: 可选，用于指定原始输入状态，用于区分用户输入和求解结果
        """
        if input_state is None:
            # 如果没有提供输入状态，则使用当前输入作为输入状态
            self.get_board_from_entries()
            input_state = [row.copy() for row in self.board]
        
        for i in range(self.n):
            for j in range(self.n):
                entry = self.entries[i][j]
                value = self.board[i][j]
                entry.setText(value)
                
                # 更新文字颜色
                current_style = entry.styleSheet()
                new_style = '; '.join([s for s in current_style.split('; ') if not s.startswith('color:')])
                
                # 如果是新解出的数字（不在输入状态中），显示为绿色
                if value and (not input_state[i][j] or input_state[i][j] != value):
                    new_style += '; color: #008000'  # 绿色
                elif value:
                    new_style += '; color: #FF0000'  # 红色（用户输入）
                
                entry.setStyleSheet(new_style)
    
    def load_history(self):
        """从文件加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            self.history = []

    def save_history(self):
        """保存历史记录到文件"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def solve(self):
        """求解当前数独"""
        # 获取用户的原始输入（红色数字）
        original_input = self.get_original_input()
        
        # 检查是否有足够的初始值
        filled_cells = sum(1 for row in original_input for cell in row if cell != '')
        if filled_cells == 0:
            QMessageBox.information(self, "提示", "请先输入数独的初始值")
            return
            
        # 深拷贝当前输入用于比较
        current = [[cell for cell in row] for row in original_input]
        
        # 检查原始输入是否与上次求解时相同
        if hasattr(self, 'last_input') and self.last_input is not None:
            if all(current[i][j] == self.last_input[i][j] 
                  for i in range(self.n) 
                  for j in range(self.n)):
                QMessageBox.information(self, "提示", "输入未发生改变，无需重新计算")
                return
        
        # 保存当前输入状态以供下次比较
        self.last_input = current
        
        # 使用原始输入进行求解
        self.board = [row.copy() for row in original_input]
        
        # 复制棋盘，避免修改原始数据
        board_copy = [row.copy() for row in self.board]
        input_board = [row.copy() for row in self.board]  # 保存输入状态
        
        if solve_sudoku(board_copy, self.symbols):
            # 先保存结果
            result_board = [row.copy() for row in board_copy]
            # 更新显示
            self.board = result_board
            self.update_entries_from_board(input_state=input_board)  # 传入原始输入状态
            
            # 保存到历史记录
            timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            history_entry = {
                "input": input_board,
                "result": result_board,
                "symbols": self.symbols,
                "size": self.box_size
            }
            self.history.append((timestamp, history_entry))
            self.save_history()  # 保存到文件
            
            self.statusBar().showMessage("数独已成功求解")
        else:
            QMessageBox.critical(self, "错误", "无法解出此数独，可能输入有误或数独无解")
            self.statusBar().showMessage("数独无解")
    
    def clear(self):
        """清空数独棋盘"""
        for i in range(self.n):
            for j in range(self.n):
                self.board[i][j] = ''
                entry = self.entries[i][j]
                entry.setText('')
                # 清除颜色样式但保留其他样式
                current_style = entry.styleSheet()
                new_style = '; '.join([s for s in current_style.split('; ') if not s.startswith('color:')])
                entry.setStyleSheet(new_style)
        
        # 重置所有输入状态
        self.current_input = [['' for _ in range(self.n)] for _ in range(self.n)]
        self.last_input = [['' for _ in range(self.n)] for _ in range(self.n)]
        
        self.statusBar().showMessage("数独已清空")
    
    def show_history(self):
        """显示历史记录对话框"""
        if not self.history:
            QMessageBox.information(self, "提示", "暂无历史记录")
            return
        
        dialog = HistoryDialog(self.history, self)
        dialog.exec_()
    
    def start_challenge(self):
        """启动挑战模式"""
        dialog = ChallengeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            difficulty, size = dialog.get_settings()
            challenge = ChallengeMode(difficulty, size, self)
            challenge.show()

def main():
    # 直接显示GUI，忽略命令行参数
    app = QApplication([])
    window = SudokuSolverApp()
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()