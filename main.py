# main.py - v1.3 支持可视化拖入框 + 全局拖拽 + 智能识别
import sys
import os
from datetime import datetime
from math import ceil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QPushButton,
    QVBoxLayout, QWidget, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi
from pypdf import PdfReader, PdfWriter

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
ui_path = os.path.join(script_dir, "bank_sorter.ui")

class DropLabel(QLabel):
    """支持拖放的可视化区域"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # -------设置拖放区域ui设计---------
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setMinimumHeight(80)
        self._normal_style = """
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 8px;
                background-color: #f9f9f9;
                color: #555;
                padding: 16px;
                font-size: 14px;
            }
        """
        self._hover_style = """
            QLabel {
                border: 2px solid #4CAF50;
                border-radius: 8px;
                background-color: #e8f5e9;
                color: #2e7d32;
                padding: 16px;
                font-size: 14px;
            }
        """
        self.setStyleSheet(self._normal_style)
        self.setText("📁 将 PDF 文件拖到此处\n（仅支持单个 PDF）")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].toLocalFile().lower().endswith('.pdf'):
                event.acceptProposedAction()
                self.setStyleSheet(self._hover_style)
            else:
                event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._normal_style)

    def dropEvent(self, event):
        self.setStyleSheet(self._normal_style)
        urls = event.mimeData().urls()
        if len(urls) != 1:
            return
        file_path = urls[0].toLocalFile()
        if not file_path.lower().endswith('.pdf'):
            return

        main_window = self.window()
        if hasattr(main_window, '_do_sort') and hasattr(main_window, 'detect_bank_from_filename'):
            bank_type = main_window.detect_bank_from_filename(file_path)
            if bank_type is None:
                QMessageBox.warning(
                    main_window,
                    "拖拽识别失败",
                    f"文件名未包含“工行”或“农行”：\n{os.path.basename(file_path)}\n\n"
                    "请重命名后重试，或使用下方按钮手动选择。"
                )
                return
            main_window._do_sort(file_path, bank_type)


class BankSorterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("银行回单排序 v1.4")

        # 尝试加载 .ui
        try:
            loadUi(ui_path, self)
            print("✅ .ui 加载成功")

            # 🔥 关键：查找 drop_label 并替换为 DropLabel
            layout = self.centralwidget.layout()
            if layout and hasattr(self, 'drop_label'):
                for i in range(layout.count()):
                    widget = layout.itemAt(i).widget()
                    if widget is self.drop_label:
                        new_drop = DropLabel()
                        layout.replaceWidget(self.drop_label, new_drop)
                        self.drop_label.deleteLater()
                        print("✅ drop_label 已替换为可拖放版本")
                        break
            else:
                raise Exception("未找到布局或 drop_label")

        except Exception as e:
            print(f"⚠️ .ui 加载失败或无 drop_label，使用动态界面: {e}")
            self._create_fallback_ui()

        # 连接按钮
        self.btn_sort_abc.clicked.connect(lambda: self.handle_manual_sort("abc"))
        self.btn_sort_icbc.clicked.connect(lambda: self.handle_manual_sort("icbc"))
        self.btn_smart_sort.clicked.connect(self.handle_smart_sort)

        self.setAcceptDrops(True)



    def _create_fallback_ui(self):
        """动态创建完整界面（含拖入框）"""
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        self.btn_sort_abc = QPushButton("农行打印排序")
        self.btn_sort_icbc = QPushButton("工行打印排序")
        self.btn_smart_sort = QPushButton("智能识别并排序")
        self.drop_area = DropLabel()

        layout.addWidget(self.btn_sort_abc)
        layout.addWidget(self.btn_sort_icbc)
        layout.addWidget(self.btn_smart_sort)
        layout.addWidget(self.drop_area)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    # ======================
    # 核心处理逻辑
    # ======================
    def create_blank_page(self):
        writer = PdfWriter()
        return writer.add_blank_page(width=595, height=842)  # A4: 595x842 pt

    def process_pdf_abc(self, input_path):
        return self._process_pdf(input_path, cols=3, bank_name="农行")

    def process_pdf_icbc(self, input_path):
        return self._process_pdf(input_path, cols=2, bank_name="工行")

    def _process_pdf(self, input_path, cols, bank_name):
        reader = PdfReader(input_path)
        original_pages = list(reader.pages)
        n = len(original_pages)

        R = ceil(n / cols)
        target_total = cols * R
        blank_count = target_total - n

        pages = original_pages[:]
        if blank_count > 0:
            blank = self.create_blank_page()
            pages.extend([blank] * blank_count)

        new_order = []
        for row in range(R):
            for col in range(cols):
                idx = col * R + row
                if idx < len(pages):
                    new_order.append(idx)

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{bank_name}_拆分后_排序打印回单_{timestamp}.pdf"
        output_path = os.path.join(desktop, output_filename)

        writer = PdfWriter()
        for idx in new_order:
            writer.add_page(pages[idx])
        with open(output_path, "wb") as f:
            writer.write(f)

        return {
            "原始页数": n,
            "行数R": R,
            "补齐至": target_total,
            "补空页数": blank_count,
            "输出总页": len(new_order),
            "文件路径": output_path,
            "银行": bank_name
        }

    def show_result_message(self, info):
        msg = (
            f"✅ {info['银行']}排序成功！\n\n"
            f"原始页数: {info['原始页数']}\n"
            f"补空页数: {info['补空页数']}\n"
            f"输出总页: {info['输出总页']}\n"
            f"文件已保存到桌面：\n{os.path.basename(info['文件路径'])}"
        )
        QMessageBox.information(self, "完成", msg)

    def detect_bank_from_filename(self, filepath):
        basename = os.path.basename(filepath).lower()
        if "农行" in basename or "农业银行" in basename:
            return "abc"
        elif "工行" in basename or "工商银行" in basename:
            return "icbc"
        else:
            return None

    def handle_manual_sort(self, bank_type):


        # 默认目录用桌面兜底
        default_dir = os.path.expanduser("~/Desktop")

        if not os.path.exists(default_dir):
            default_dir = os.path.expanduser("~\\Desktop")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择已分割的回单 PDF", default_dir, "PDF Files (*.pdf)"
        )
        if not file_path:
            return
        self._do_sort(file_path, bank_type)

    def handle_smart_sort(self):
        default_dir = r"C:\Users\Lenovo\Desktop\BaiduSyncdisk\工作\2025"
        if not os.path.exists(default_dir):
            default_dir = os.path.expanduser("~\\Desktop")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择回单 PDF（将自动识别银行）", default_dir, "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        bank_type = self.detect_bank_from_filename(file_path)
        if bank_type is None:
            QMessageBox.warning(
                self,
                "无法识别",
                "文件名中未检测到“工行”或“农行”，请手动选择处理方式。"
            )
            return
        self._do_sort(file_path, bank_type)

    def _do_sort(self, file_path, bank_type):
        try:
            if bank_type == "abc":
                info = self.process_pdf_abc(file_path)
            elif bank_type == "icbc":
                info = self.process_pdf_icbc(file_path)
            else:
                raise ValueError("未知银行类型")
            self.show_result_message(info)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理失败：\n{str(e)}")

    # ======================
    # 全局拖拽支持（兼容）
    # ======================
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].toLocalFile().lower().endswith('.pdf'):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if len(urls) != 1:
            return
        file_path = urls[0].toLocalFile()
        if not file_path.lower().endswith('.pdf'):
            return

        bank_type = self.detect_bank_from_filename(file_path)
        if bank_type is None:
            QMessageBox.warning(
                self,
                "拖拽识别失败",
                f"文件名未包含“工行”或“农行”：\n{os.path.basename(file_path)}\n\n"
                "请重命名后重试，或使用下方按钮手动选择。"
            )
            return
        self._do_sort(file_path, bank_type)

    def closeEvent(self, event):
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BankSorterApp()
    window.resize(340, 280)
    window.show()
    sys.exit(app.exec_())