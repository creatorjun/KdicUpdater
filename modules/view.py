from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QListWidget, QFileDialog, QProgressBar,
                            QLabel, QListWidgetItem, QSplitter, QPlainTextEdit,
                            QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize # pyqtSlot 추가
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QPen
import os
from datetime import datetime

class WimListItem(QListWidgetItem):
    """WIM 파일 상세 정보를 담는 커스텀 리스트 아이템"""

    # 클래스 변수로 아이콘 저장
    checked_icon = None
    unchecked_icon = None

    @classmethod
    def create_icons(cls):
        """10x10 크기의 체크/언체크 아이콘 생성"""
        if cls.checked_icon is None:
            # 체크된 아이콘 (녹색 배경 + 흰색 체크마크)
            checked_pixmap = QPixmap(10, 10)
            checked_pixmap.fill(Qt.GlobalColor.green)
            painter = QPainter(checked_pixmap)
            painter.setPen(QPen(Qt.GlobalColor.white, 1))
            painter.drawLine(2, 5, 4, 7)
            painter.drawLine(4, 7, 8, 3)
            painter.end()
            cls.checked_icon = QIcon(checked_pixmap)

            # 체크 안된 아이콘 (흰색 배경 + 검은 테두리)
            unchecked_pixmap = QPixmap(10, 10)
            unchecked_pixmap.fill(Qt.GlobalColor.white)
            painter = QPainter(unchecked_pixmap)
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            painter.drawRect(0, 0, 9, 9)
            painter.end()
            cls.unchecked_icon = QIcon(unchecked_pixmap)

    def __init__(self, wim_info):
        super().__init__()
        WimListItem.create_icons()

        self.file_path = wim_info.get('file_path', 'N/A')
        self.file_name = os.path.basename(self.file_path)
        self.win_name = wim_info.get('name', 'N/A')
        self.win_version = wim_info.get('version', 'N/A')
        self.win_build = wim_info.get('build', 'N/A')
        self.file_size = self.get_file_size(self.file_path)

        self.is_selected = True  # 기본값: 선택됨

        # 표시 텍스트 설정 (여러 줄로)
        display_text = (
            f"{self.file_name} ({self.file_size})\n"
            f"    - 버전: {self.win_version} (빌드: {self.win_build}) / 이름: {self.win_name}"
        )
        self.setText(display_text)
        self.setFont(QFont("Segoe UI", 9))

        self.update_icon()
        self.setToolTip(f"경로: {self.file_path}")

    def get_file_size(self, file_path):
        """파일 크기를 읽기 쉬운 형태로 변환"""
        try:
            size_bytes = os.path.getsize(file_path)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024**2:
                return f"{size_bytes/1024:.1f} KB"
            elif size_bytes < 1024**3:
                return f"{size_bytes/(1024**2):.1f} MB"
            else:
                return f"{size_bytes/(1024**3):.1f} GB"
        except FileNotFoundError:
            return "N/A"
        except Exception:
            return "Unknown"

    def toggle_selection(self):
        """선택 상태 토글"""
        self.is_selected = not self.is_selected
        self.update_icon()

    def set_selection(self, selected):
        """선택 상태 직접 설정"""
        self.is_selected = selected
        self.update_icon()

    def update_icon(self):
        """아이콘 업데이트"""
        icon = self.checked_icon if self.is_selected else self.unchecked_icon
        self.setIcon(icon)


class View(QWidget):
    # 시그널 정의 (클래스 속성으로 정의)
    folder_selected = pyqtSignal(str)
    start_update = pyqtSignal(list)
    cancel_update = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.selected_folder = ""
        self.is_updating = False
        self.is_scanning = False
        self.initUI()

    def initUI(self):
        # 윈도우 타이틀과 아이콘 설정
        self.setWindowTitle("KdicUpdater - WIM 파일 업데이트 매니저 v1.0")
        self.setGeometry(100, 100, 800, 600)

        # 아이콘 설정
        icon_path = "icon/kdic.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            # 절대 경로로 다시 시도
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon", "kdic.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet(self.get_stylesheet())

        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # 상단: 프로그램 헤더
        header_layout = QHBoxLayout()
        header_label = QLabel("KdicUpdater")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                color: #212529;
                padding: 10px;
            }
        """)

        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #6c757d;
                padding: 10px;
            }
        """)

        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(version_label)
        main_layout.addLayout(header_layout)

        # 폴더 선택 영역
        folder_group = self.create_folder_selection_group()
        main_layout.addWidget(folder_group)

        # 중간: 메인 작업 영역 (분할)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_widget = self.create_wim_list_group()
        right_widget = self.create_log_group()
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

        # 하단: 컨트롤 영역
        control_group = self.create_control_group()
        main_layout.addWidget(control_group)

        self.setLayout(main_layout)
        self.update_ui_state()

    def create_folder_selection_group(self):
        """폴더 선택 영역 생성"""
        group = QGroupBox("작업 폴더 선택")
        layout = QHBoxLayout()

        self.folder_btn = QPushButton("📂 폴더 선택")
        self.folder_btn.clicked.connect(self.open_folder_dialog)
        self.folder_btn.setFixedHeight(35)

        self.folder_label = QLabel("선택된 폴더가 없습니다.")
        self.folder_label.setStyleSheet("color: #6c757d; font-style: italic;")

        layout.addWidget(self.folder_btn)
        layout.addWidget(self.folder_label, 1)

        group.setLayout(layout)
        return group

    def create_wim_list_group(self):
        """WIM 파일 리스트 영역 생성"""
        group = QGroupBox("WIM 파일 목록")
        layout = QVBoxLayout()

        checkbox_layout = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("전체 선택")
        self.select_all_checkbox.stateChanged.connect(self.toggle_all_selection)

        self.selection_status_label = QLabel("선택: 0/0개")
        self.selection_status_label.setStyleSheet("color: #495057; font-size: 8pt;")

        checkbox_layout.addWidget(self.select_all_checkbox)
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self.selection_status_label)
        layout.addLayout(checkbox_layout)

        self.wim_list = QListWidget()
        self.wim_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.wim_list.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.wim_list)

        help_label = QLabel("각 파일을 클릭하여 업데이트 대상을 선택/해제할 수 있습니다.")
        help_label.setStyleSheet("color: #6c757d; font-size: 8pt; font-style: italic; padding: 5px;")
        layout.addWidget(help_label)

        group.setLayout(layout)
        return group

    def create_log_group(self):
        """로그 영역 생성"""
        group = QGroupBox("작업 로그")
        layout = QVBoxLayout()
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)
        self.log_text.appendPlainText("KdicUpdater가 시작되었습니다.")
        self.log_text.appendPlainText("폴더를 선택하여 WIM 파일을 스캔하세요.")
        layout.addWidget(self.log_text)
        group.setLayout(layout)
        return group

    def create_control_group(self):
        """컨트롤 영역 생성"""
        group = QGroupBox("작업 제어")
        layout = QVBoxLayout()

        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("업데이트 시작")
        self.start_btn.clicked.connect(self.start_update_process)
        self.start_btn.setFixedHeight(40)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd; color: white; font-weight: bold;
                border: none; border-radius: 5px; font-size: 11pt;
            }
            QPushButton:hover { background-color: #0b5ed7; }
            QPushButton:disabled { background-color: #6c757d; color: #dee2e6; }
        """)

        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.cancel_update.emit)
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545; color: white; font-weight: bold;
                border: none; border-radius: 5px;
            }
            QPushButton:hover { background-color: #bb2d3b; }
            QPushButton:disabled { background-color: #6c757d; color: #dee2e6; }
        """)
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        progress_layout = QVBoxLayout()
        self.status_label = QLabel("대기 중...")
        self.status_label.setStyleSheet("color: #495057; font-weight: bold; font-size: 10pt;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #dee2e6; border-radius: 8px; text-align: center;
                font-weight: bold; background-color: #f8f9fa; color: #495057;
            }
            QProgressBar::chunk { background-color: #0d6efd; border-radius: 6px; }
        """)
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)

        group.setLayout(layout)
        return group

    def get_stylesheet(self):
        """전체 UI에 적용될 스타일시트"""
        return """
            QWidget {
                font-family: 'Segoe UI', 'Malgun Gothic', Arial, sans-serif;
                font-size: 9pt; background-color: #f8f9fa; color: #212529;
            }
            QGroupBox {
                font-weight: bold; border: 2px solid #dee2e6; border-radius: 8px;
                margin-top: 12px; padding-top: 10px; background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 15px; padding: 0 8px;
                color: #495057; font-weight: bold;
            }
            QPushButton {
                background-color: #ffffff; border: 1px solid #dee2e6;
                border-radius: 5px; padding: 8px; min-width: 80px;
                font-weight: 500; color: #495057;
            }
            QPushButton:hover {
                background-color: #e9ecef; border-color: #adb5bd; color: #212529;
            }
            QPushButton:disabled {
                background-color: #f8f9fa; color: #6c757d; border-color: #dee2e6;
            }
            QListWidget {
                border: 1px solid #dee2e6; border-radius: 5px; background-color: white;
            }
            QListWidget::item {
                padding: 8px 12px; border-bottom: 1px solid #f1f3f4;
            }
            QListWidget::item:hover { background-color: #f0f8ff; }
            QListWidget::item:selected { background-color: #e7f3ff; color: #212529; }
            QPlainTextEdit {
                border: 1px solid #dee2e6; border-radius: 5px;
                background-color: #ffffff; color: #212529;
                font-family: 'Consolas', 'Monaco', monospace; font-size: 8pt;
            }
            QCheckBox { spacing: 10px; font-weight: 500; }
            QCheckBox::indicator {
                width: 10px; height: 10px; border: 1px solid #000;
                border-radius: 1px; background-color: #fff;
            }
            QCheckBox::indicator:checked { background-color: #000; }
            QCheckBox::indicator:indeterminate { background-color: #666; }
        """

    @pyqtSlot()
    def open_folder_dialog(self):
        """폴더 선택 다이얼로그 열기"""
        if self.is_scanning or self.is_updating: return

        folder = QFileDialog.getExistingDirectory(self, "WIM 파일이 있는 폴더 선택", self.selected_folder or ".")
        if folder:
            self.selected_folder = folder
            self.folder_label.setText(folder)
            self.folder_label.setStyleSheet("color: #212529; font-weight: 500;")
            self.wim_list.clear()
            self.folder_selected.emit(folder)

    @pyqtSlot(bool)
    def set_scan_mode(self, scanning):
        """스캔 모드 UI 설정"""
        self.is_scanning = scanning
        self.folder_btn.setEnabled(not scanning)
        self.start_btn.setEnabled(False) # 스캔 중 및 스캔 완료 직후에는 비활성화

        if scanning:
            self.status_label.setText("WIM 파일 정보 스캔 중...")
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.status_label.setText("대기 중...")

    @pyqtSlot(list)
    def update_wim_list(self, wim_files_info):
        """스캔 완료 후 WIM 리스트 위젯 업데이트"""
        self.wim_list.clear()
        if not wim_files_info:
            self.add_log("표시할 WIM 파일 정보가 없습니다.")
        else:
            for wim_info in wim_files_info:
                item = WimListItem(wim_info)
                self.wim_list.addItem(item)
            self.add_log(f"총 {len(wim_files_info)}개의 WIM 파일 정보를 불러왔습니다.")
        self.update_ui_state()

    @pyqtSlot(int)
    def toggle_all_selection(self, state):
        """전체 선택/해제 체크박스 상태 변경 시"""
        if self.is_updating: return

        is_checked = (Qt.CheckState(state) == Qt.CheckState.Checked)
        for i in range(self.wim_list.count()):
            item = self.wim_list.item(i)
            if item:
                item.set_selection(is_checked)

        self.update_ui_state()
        self.add_log(f"모든 파일 {'선택' if is_checked else '선택 해제'}됨")

    @pyqtSlot(QListWidgetItem)
    def on_item_clicked(self, item):
        """리스트 아이템 클릭 시 선택 상태 토글"""
        if self.is_updating or not item: return
        item.toggle_selection()
        self.update_ui_state()

    def get_selected_files(self):
        """선택된 항목의 파일 경로 리스트 반환"""
        return [self.wim_list.item(i).file_path for i in range(self.wim_list.count()) if self.wim_list.item(i).is_selected]

    def start_update_process(self):
        """업데이트 프로세스 시작"""
        selected_files = self.get_selected_files()
        if not selected_files:
            self.add_log("업데이트할 WIM 파일을 선택해주세요.")
            return

        self.add_log(f"{len(selected_files)}개 파일의 업데이트를 시작합니다...")
        self.start_update.emit(selected_files)

    def set_update_mode(self, updating):
        """업데이트 모드 UI 설정"""
        self.is_updating = updating
        self.start_btn.setEnabled(not updating)
        self.cancel_btn.setEnabled(updating)
        self.folder_btn.setEnabled(not updating)
        self.select_all_checkbox.setEnabled(not updating)
        self.wim_list.setEnabled(not updating)

        if updating:
            self.status_label.setText("업데이트 진행 중...")
        else:
            self.status_label.setText("대기 중...")

    def reset_ui_immediately(self):
        """즉시 UI 초기화 (취소 시 사용)"""
        self.is_updating = False
        self.set_update_mode(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("업데이트가 취소되었습니다.")
        self.update_ui_state()

    def update_ui_state(self):
        """UI 상태 업데이트"""
        total_count = self.wim_list.count()
        selected_count = len(self.get_selected_files())

        # 업데이트 중이 아닐 때만 시작 버튼 활성화
        if not self.is_updating and not self.is_scanning:
            self.start_btn.setEnabled(selected_count > 0)

        self.selection_status_label.setText(f"선택: {selected_count}/{total_count}개")

        # 체크박스 시그널을 잠시 비활성화하여 무한 루프 방지
        self.select_all_checkbox.blockSignals(True)
        if total_count == 0:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
            self.select_all_checkbox.setEnabled(False)
        elif selected_count == total_count:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Checked)
            self.select_all_checkbox.setEnabled(True)
        elif selected_count == 0:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
            self.select_all_checkbox.setEnabled(True)
        else:
            self.select_all_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
            self.select_all_checkbox.setEnabled(True)
        self.select_all_checkbox.blockSignals(False)

    def add_log(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.appendPlainText(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def update_progress(self, value, message=""):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)

    def reset_ui_after_completion(self):
        """작업 완료 후 UI 리셋"""
        self.is_updating = False
        self.set_update_mode(False)
        self.progress_bar.setValue(100)
        self.status_label.setText("업데이트 완료")
        self.update_ui_state()