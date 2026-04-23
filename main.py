# main.py - v2.0 极简流畅美学版 (Fluent Design)
import sys
import os
import logging
from datetime import datetime
from math import ceil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QGraphicsDropShadowEffect,
    QDialog, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QFont, QColor, QPainter, QPainterPath, QPen
from pypdf import PdfReader, PdfWriter

# ============ 常量 ============
A4_WIDTH, A4_HEIGHT = 595, 842
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")

# ============ 日志配置 ============
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============ 现代级高级调色板 (Tailwind 风格) ============
COLORS = {
    "bg_window": "#F8FAFC",  # 窗口底色 - 极浅灰蓝 (Slate 50)
    "bg_card": "#FFFFFF",  # 卡片底色 - 纯白
    "primary": "#6366F1",  # 主题色 - 靛蓝 (Indigo 500)
    "primary_hover": "#4F46E5",  # 主题色悬浮 (Indigo 600)
    "primary_pressed": "#4338CA",  # 主题色按下 (Indigo 700)
    "text_title": "#0F172A",  # 标题文字 (Slate 900)
    "text_main": "#334155",  # 正文文字 (Slate 700)
    "text_muted": "#64748B",  # 弱化文字 (Slate 500)
    "border": "#E2E8F0",  # 边框色 (Slate 200)
    "border_focus": "#818CF8",  # 边框高亮 (Indigo 400)
    "drop_bg": "#F8FAFC",  # 拖拽区默认背景
    "drop_bg_hover": "#EEF2FF"  # 拖拽区高亮背景 (Indigo 50)
}

# ============ 全局字体设定 ============
FONT_FAMILY = '"Segoe UI Variable", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, sans-serif'

# ============ 核心样式表 ============
STYLE_GLOBAL = f"""
QMainWindow {{ background-color: {COLORS['bg_window']}; }}
QWidget#main_card {{
    background-color: {COLORS['bg_card']};
    border-radius: 20px;
    border: 1px solid {COLORS['border']};
}}
"""


class DropZone(QWidget):
    """自定义绘制的现代拖拽区（实现完美的圆角虚线边框）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("drop_zone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(180)
        self.is_hovering = False

        # 布局和文字
        layout = QVBoxLayout(self)
        self.icon_label = QLabel("📥")
        self.icon_label.setStyleSheet("font-size: 36px; margin-bottom: 5px;")
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.text_label = QLabel("将 PDF 文件拖拽至此处\n支持 .pdf 格式")
        self.text_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-family: {FONT_FAMILY};
            font-size: 14px;
            font-weight: 500;
        """)
        self.text_label.setAlignment(Qt.AlignCenter)

        layout.addStretch()
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addStretch()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景
        path = QPainterPath()
        path.addRoundedRect(1, 1, self.width() - 2, self.height() - 2, 16, 16)
        painter.fillPath(path, QColor(COLORS['drop_bg_hover'] if self.is_hovering else COLORS['drop_bg']))

        # 绘制虚线边框
        pen = QPen(QColor(COLORS['primary'] if self.is_hovering else COLORS['border']))
        pen.setWidth(2)
        pen.setStyle(Qt.DashLine)
        pen.setDashPattern([6, 4])  # 现代感的虚线比例
        painter.setPen(pen)
        painter.drawPath(path)

    def dragEnterEvent(self, event):
        if self._is_valid_pdf_drop(event):
            event.acceptProposedAction()
            self.is_hovering = True
            self.icon_label.setText("✨")
            self.text_label.setText("松开鼠标立即处理")
            self.text_label.setStyleSheet(
                f"color: {COLORS['primary']}; font-family: {FONT_FAMILY}; font-size: 15px; font-weight: bold;")
            self.update()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.is_hovering = False
        self.icon_label.setText("📥")
        self.text_label.setText("将 PDF 文件拖拽至此处\n支持 .pdf 格式")
        self.text_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-family: {FONT_FAMILY}; font-size: 14px; font-weight: 500;")
        self.update()

    def dropEvent(self, event):
        self.dragLeaveEvent(event)
        urls = event.mimeData().urls()
        if len(urls) != 1: return
        file_path = urls[0].toLocalFile()
        if not file_path.lower().endswith('.pdf'): return

        main_window = self.window()
        if hasattr(main_window, 'handle_file_drop'):
            main_window.handle_file_drop(file_path)

    @staticmethod
    def _is_valid_pdf_drop(event):
        if not event.mimeData().hasUrls(): return False
        urls = event.mimeData().urls()
        return len(urls) == 1 and urls[0].toLocalFile().lower().endswith('.pdf')


class ModernDialog(QDialog):
    """现代化的提示弹窗，替代原生的 QMessageBox"""

    def __init__(self, title, message, is_error=False, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 主卡片
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 16px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 20)
        card_layout.setSpacing(12)

        # 图标与标题
        icon_color = "#EF4444" if is_error else COLORS['primary']
        icon_text = "❌" if is_error else "✅"

        title_lbl = QLabel(f"<span style='color:{icon_color}; font-size:18px;'>{icon_text}</span> &nbsp;{title}")
        title_lbl.setStyleSheet(
            f"color: {COLORS['text_title']}; font-size: 16px; font-weight: bold; font-family: {FONT_FAMILY}; border: none;")

        # 内容正文
        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(
            f"color: {COLORS['text_main']}; font-size: 13px; line-height: 1.5; font-family: {FONT_FAMILY}; border: none;")

        # 确认按钮
        btn = QPushButton("我知道了")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_window']};
                color: {COLORS['text_title']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{ background-color: #F1F5F9; border-color: {COLORS['text_muted']}; }}
        """)
        btn.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)

        card_layout.addWidget(title_lbl)
        card_layout.addWidget(msg_lbl)
        card_layout.addSpacing(10)
        card_layout.addLayout(btn_layout)

        layout.addWidget(card)


def add_shadow(widget, blur=30, offset_y=10, opacity=25):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(0, 0, 0, opacity))
    shadow.setOffset(0, offset_y)
    widget.setGraphicsEffect(shadow)


class BankSorterApp(QMainWindow):
    """银行回单排序工具 v2.0 - Fluent Design"""

    BANK_CONFIGS = {
        "abc": (3, "农行", "🏦"),
        "icbc": (2, "工行", "🏦"),
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("回单智排 Pro")
        self.setStyleSheet(STYLE_GLOBAL)
        self.setFixedSize(540, 580)
        self._create_ui()
        self.setAcceptDrops(True)

    def _create_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(30, 35, 30, 35)

        # ========== 核心内容卡片 ==========
        self.card = QWidget()
        self.card.setObjectName("main_card")
        add_shadow(self.card)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(30, 35, 30, 35)
        card_layout.setSpacing(25)

        # 1. 顶部标题区
        title_layout = QVBoxLayout()
        title_layout.setSpacing(6)

        title = QLabel("银行回单排序处理")
        title.setStyleSheet(
            f"color: {COLORS['text_title']}; font-size: 22px; font-weight: 800; font-family: {FONT_FAMILY};")

        subtitle = QLabel("智能分析 PDF 结构，自动按行/列重排并补齐空白页")
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; font-family: {FONT_FAMILY};")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        card_layout.addLayout(title_layout)

        # 2. 拖拽交互区
        self.drop_area = DropZone()
        card_layout.addWidget(self.drop_area)

        # 3. 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"border: none; background-color: {COLORS['border']}; max-height: 1px;")
        card_layout.addWidget(line)

        # 4. 操作按钮区
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(12)

        # 主按钮：智能识别
        self.btn_smart = QPushButton("✨ 智能识别并排序 (推荐)")
        self.btn_smart.setCursor(Qt.PointingHandCursor)
        self.btn_smart.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']}; color: white;
                border: none; border-radius: 10px; padding: 14px;
                font-size: 15px; font-weight: bold; font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{ background-color: {COLORS['primary_hover']}; }}
            QPushButton:pressed {{ background-color: {COLORS['primary_pressed']}; }}
        """)

        # 辅助按钮组
        sub_btn_layout = QHBoxLayout()
        sub_btn_layout.setSpacing(12)

        btn_style_secondary = f"""
            QPushButton {{
                background-color: transparent; color: {COLORS['text_main']};
                border: 1.5px solid {COLORS['border']}; border-radius: 10px;
                padding: 10px; font-size: 13px; font-weight: 600; font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{ background-color: {COLORS['bg_window']}; border-color: {COLORS['text_muted']}; color: {COLORS['text_title']}; }}
            QPushButton:pressed {{ background-color: {COLORS['border']}; }}
        """

        self.btn_abc = QPushButton("🏦 农行 (3列)")
        self.btn_abc.setCursor(Qt.PointingHandCursor)
        self.btn_abc.setStyleSheet(btn_style_secondary)

        self.btn_icbc = QPushButton("🏦 工行 (2列)")
        self.btn_icbc.setCursor(Qt.PointingHandCursor)
        self.btn_icbc.setStyleSheet(btn_style_secondary)

        sub_btn_layout.addWidget(self.btn_abc)
        sub_btn_layout.addWidget(self.btn_icbc)

        btn_layout.addWidget(self.btn_smart)
        btn_layout.addLayout(sub_btn_layout)
        card_layout.addLayout(btn_layout)

        main_layout.addWidget(self.card)

        # 连接信号
        self.btn_smart.clicked.connect(self._smart_sort)
        self.btn_abc.clicked.connect(lambda: self._select_and_sort("abc"))
        self.btn_icbc.clicked.connect(lambda: self._select_and_sort("icbc"))

    # ====================== 核心处理逻辑 (保持原样) ======================
    def _create_blank_page(self):
        writer = PdfWriter()
        writer.add_blank_page(width=A4_WIDTH, height=A4_HEIGHT)
        return writer.pages[0]

    def _process_pdf(self, input_path, cols, bank_name):
        reader = PdfReader(input_path)
        original_pages = list(reader.pages)
        n = len(original_pages)

        R = ceil(n / cols)
        target_total = cols * R
        blank_count = target_total - n

        pages = original_pages[:]
        if blank_count > 0:
            blank_page = self._create_blank_page()
            for _ in range(blank_count):
                pages.append(blank_page)

        new_order = []
        for row in range(R):
            for col in range(cols):
                idx = col * R + row
                if idx < len(pages):
                    new_order.append(idx)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{bank_name}_拆分后_排序打印回单_{timestamp}.pdf"
        output_path = os.path.join(DESKTOP_PATH, output_filename)

        writer = PdfWriter()
        for idx in new_order:
            writer.add_page(pages[idx])

        with open(output_path, "wb") as f:
            writer.write(f)

        return {
            "原始页数": n, "行数R": R, "补齐至": target_total,
            "补空页数": blank_count, "输出总页": len(new_order),
            "文件路径": output_path, "银行": bank_name
        }

    def _detect_bank(self, filepath):
        basename = os.path.basename(filepath).lower()
        if "农行" in basename or "农业银行" in basename:
            return "abc"
        elif "工行" in basename or "工商银行" in basename:
            return "icbc"
        return None

    def _select_and_sort(self, bank_type):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择回单 PDF", DESKTOP_PATH, "PDF Files (*.pdf)")
        if file_path: self._sort_file(file_path, bank_type)

    def _smart_sort(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择回单 PDF", DESKTOP_PATH, "PDF Files (*.pdf)")
        if not file_path: return
        bank_type = self._detect_bank(file_path)
        if bank_type is None:
            self._show_alert("无法识别", "文件名中未检测到\"工行\"或\"农行\"，请使用下方按钮手动指定格式。", True)
            return
        self._sort_file(file_path, bank_type)

    def handle_file_drop(self, file_path):
        bank_type = self._detect_bank(file_path)
        if bank_type is None:
            self._show_alert("拖拽识别失败",
                             f"文件名未包含\"工行\"或\"农行\"：\n<span style='color:{COLORS['primary']};'>{os.path.basename(file_path)}</span>\n\n请重命名后重试，或使用按钮手动选择。",
                             True)
            return
        self._sort_file(file_path, bank_type)

    def _sort_file(self, file_path, bank_type):
        try:
            cols, bank_name, _ = self.BANK_CONFIGS[bank_type]
            info = self._process_pdf(file_path, cols=cols, bank_name=bank_name)
            self._show_result(info)
        except Exception as e:
            self._show_alert("处理异常", f"PDF 处理过程中出现错误：\n{str(e)}", True)

    def _show_result(self, info):
        msg = (
            f"原始文档包含 <b>{info['原始页数']}</b> 页，已自动补充 <b>{info['补空页数']}</b> 张空白页。<br><br>"
            f"重排后共 <b>{info['输出总页']}</b> 页，文件已安全导出至桌面：<br>"
            f"<span style='color:{COLORS['primary']}; font-weight:bold;'>{os.path.basename(info['文件路径'])}</span>"
        )
        self._show_alert(f"{info['银行']}回单处理完成", msg, False)

    def _show_alert(self, title, message, is_error):
        """调用自定义现代化弹窗"""
        dialog = ModernDialog(title, message, is_error, self)
        dialog.exec_()

    # 全局拖拽拦截
    def dragEnterEvent(self, event):
        if DropZone._is_valid_pdf_drop(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if len(urls) == 1 and urls[0].toLocalFile().lower().endswith('.pdf'):
            self.handle_file_drop(urls[0].toLocalFile())


if __name__ == "__main__":
    # 启用高 DPI 缩放支持以保证文字锐利
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = BankSorterApp()
    window.show()
    sys.exit(app.exec_())