from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QListWidget, QFileDialog, QProgressBar, 
                            QLabel, QListWidgetItem, QSplitter, QPlainTextEdit,
                            QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QPen
import os
import sys

class WimListItem(QListWidgetItem):
    """WIM 파일 정보를 담는 커스텀 리스트 아이템 (아이콘 기반 선택)"""
    
    # 클래스 변수로 아이콘 저장
    checked_icon = None
    unchecked_icon = None
    
    @classmethod
    def create_icons(cls):
        """10x10 크기의 체크/언체크 아이콘 생성"""
        # 체크된 아이콘 (녹색 배경 + 흰색 체크마크)
        checked_pixmap = QPixmap(10, 10)
        checked_pixmap.fill(Qt.GlobalColor.green)
        painter = QPainter(checked_pixmap)
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        # 간단한 체크마크 그리기 (V 모양)
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
    
    def __init__(self, file_path):
        super().__init__()
        # 아이콘이 없으면 생성
        if WimListItem.checked_icon is None:
            WimListItem.create_icons()
            
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.file_size = self.get_file_size(file_path)
        self.is_selected = True  # 기본값: 선택됨
        
        # 표시 텍스트 설정
        display_text = f"{self.file_name} ({self.file_size})"
        self.setText(display_text)
        
        # 아이콘 설정
        self.update_icon()
        
        # 툴팁 설정
        self.setToolTip(f"경로: {file_path}\n크기: {self.file_size}\n\n클릭하여 선택/해제하세요.")
    
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
        except:
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
    # 시그널 정의
    folder_selected = pyqtSignal(str)  # 폴더 선택 시그널
    start_update = pyqtSignal(list)    # 업데이트 시작 시그널
    cancel_update = pyqtSignal()       # 업데이트 취소 시그널
    
    def __init__(self):
        super().__init__()
        self.selected_folder = ""
        self.wim_files = []
        self.is_updating = False  # 업데이트 진행 상태
        self.initUI()
        
    def initUI(self):
        # 윈도우 타이틀과 아이콘 설정
        self.setWindowTitle("KdicUpdater - WIM 파일 업데이트 매니저 v1.0")
        self.setGeometry(100, 100, 800, 600)
        
        # 아이콘 설정 (윈도우별 아이콘)
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
        
        # 좌측: WIM 파일 리스트
        left_widget = self.create_wim_list_group()
        splitter.addWidget(left_widget)
        
        # 우측: 로그 영역
        right_widget = self.create_log_group()
        splitter.addWidget(right_widget)
        
        # 분할 비율 설정 (7:3)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter)
        
        # 하단: 컨트롤 영역
        control_group = self.create_control_group()
        main_layout.addWidget(control_group)
        
        self.setLayout(main_layout)
        
        # 초기 상태 설정
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
        """WIM 파일 리스트 영역 생성 - 아이콘 기반 선택"""
        group = QGroupBox("WIM 파일 목록")
        layout = QVBoxLayout()
        
        # 전체 선택/해제 체크박스와 상태 표시
        checkbox_layout = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("전체 선택")
        self.select_all_checkbox.stateChanged.connect(self.toggle_all_selection)
        
        # 선택 상태 라벨
        self.selection_status_label = QLabel("선택: 0/0개")
        self.selection_status_label.setStyleSheet("color: #495057; font-size: 8pt;")
        
        self.file_count_label = QLabel("파일 개수: 0개")
        
        checkbox_layout.addWidget(self.select_all_checkbox)
        checkbox_layout.addWidget(self.selection_status_label)
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self.file_count_label)
        
        layout.addLayout(checkbox_layout)
        
        # WIM 파일 리스트 - 아이콘 기반
        self.wim_list = QListWidget()
        self.wim_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        # 아이템 클릭 시 선택 상태 토글
        self.wim_list.itemClicked.connect(self.on_item_clicked)
        
        layout.addWidget(self.wim_list)
        
        # 도움말 라벨
        help_label = QLabel("각 파일을 클릭하여 선택/해제하세요.")
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
        self.log_text.setMaximumBlockCount(1000)  # 최대 1000줄로 제한
        
        # 기본 메시지
        self.log_text.appendPlainText("KdicUpdater가 시작되었습니다.")
        self.log_text.appendPlainText("폴더를 선택하여 WIM 파일을 스캔하세요.")
        
        layout.addWidget(self.log_text)
        
        group.setLayout(layout)
        return group
        
    def create_control_group(self):
        """컨트롤 영역 생성"""
        group = QGroupBox("작업 제어")
        layout = QVBoxLayout()
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("업데이트 시작")
        self.start_btn.clicked.connect(self.start_update_process)
        self.start_btn.setFixedHeight(40)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #dee2e6;
            }
        """)
        
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.cancel_update_process)  # 취소 시그널 연결
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #bb2d3b;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #dee2e6;
            }
        """)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 진행률 표시
        progress_layout = QVBoxLayout()
        
        self.status_label = QLabel("대기 중...")
        self.status_label.setStyleSheet("color: #495057; font-weight: bold; font-size: 10pt;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                background-color: #f8f9fa;
                color: #495057;
            }
            QProgressBar::chunk {
                background-color: #0d6efd;
                border-radius: 6px;
            }
        """)
        
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addLayout(progress_layout)
        
        group.setLayout(layout)
        return group
        
    def get_stylesheet(self):
        """KdicUpdater 전용 스타일시트"""
        return """
            QWidget {
                font-family: 'Segoe UI', 'Malgun Gothic', Arial, sans-serif;
                font-size: 9pt;
                background-color: #f8f9fa;
                color: #212529;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: white;
                color: #212529;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #495057;
                font-weight: bold;
            }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 8px;
                min-width: 80px;
                font-weight: 500;
                color: #495057;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
                color: #212529;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
                color: #212529;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                color: #6c757d;
                border-color: #dee2e6;
            }
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                color: #212529;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f1f3f4;
                color: #212529;
                min-height: 30px;
            }
            QListWidget::item:hover {
                background-color: #f0f8ff;
                color: #212529;
            }
            QListWidget::item:selected {
                background-color: #e7f3ff;
                color: #212529;
            }
            
            QPlainTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: #ffffff;
                color: #212529;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 8pt;
                selection-background-color: #0d6efd;
                selection-color: white;
            }
            
            /* 체크박스 스타일 (전체 선택용만) */
            QCheckBox {
                spacing: 10px;
                color: #212529;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 10px;
                height: 10px;
                border: 1px solid #000000;
                border-radius: 1px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #000000;
                background-color: #f8f8f8;
            }
            QCheckBox::indicator:checked {
                background-color: #000000;
                border: 1px solid #000000;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #333333;
                border: 1px solid #000000;
            }
            QCheckBox::indicator:indeterminate {
                background-color: #666666;
                border: 1px solid #000000;
            }
            
            QLabel {
                color: #495057;
            }
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                background-color: #f8f9fa;
                color: #495057;
            }
            QProgressBar::chunk {
                background-color: #0d6efd;
                border-radius: 6px;
            }
        """
        
    @pyqtSlot()
    def open_folder_dialog(self):
        """폴더 선택 다이얼로그 열기"""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "WIM 파일이 있는 폴더 선택", 
            self.selected_folder or "./"
        )
        
        if folder:
            self.selected_folder = folder
            self.folder_label.setText(f"{folder}")
            self.folder_label.setStyleSheet("color: #212529; font-weight: 500;")
            
            self.load_wim_files(folder)
            self.folder_selected.emit(folder)
            
            self.add_log(f"폴더 선택됨: {folder}")
            
    def load_wim_files(self, folder):
        """선택된 폴더에서 WIM 파일 로드"""
        self.wim_list.clear()
        self.wim_files.clear()
        
        try:
            wim_count = 0
            for file in os.listdir(folder):
                if file.lower().endswith('.wim'):
                    file_path = os.path.join(folder, file)
                    item = WimListItem(file_path)
                    self.wim_list.addItem(item)
                    self.wim_files.append(file_path)
                    wim_count += 1
                    
            self.file_count_label.setText(f"파일 개수: {wim_count}개")
            
            if wim_count > 0:
                self.add_log(f"{wim_count}개의 WIM 파일을 찾았습니다.")
                self.add_log("파일을 클릭하여 업데이트할 파일을 선택하세요.")
            else:
                self.add_log("WIM 파일이 없습니다.")
                
        except Exception as e:
            self.add_log(f"폴더 스캔 오류: {str(e)}")
            
        # UI 상태 업데이트 (기본적으로 모든 파일 선택됨)
        self.update_ui_state()
        
    @pyqtSlot(int)
    def toggle_all_selection(self, state):
        """전체 선택/해제 - 완전 수정 버전"""
        # 업데이트 중이면 무시
        if self.is_updating:
            return
            
        # 체크박스 상태를 명확하게 판단
        is_checked = (state == Qt.CheckState.Checked.value)
        
        print(f"DEBUG: toggle_all_selection called with state={state}, is_checked={is_checked}")  # 디버그
        
        # 모든 항목의 선택 상태 변경
        changed_count = 0
        for i in range(self.wim_list.count()):
            item = self.wim_list.item(i)
            if item:
                old_state = item.is_selected
                item.set_selection(is_checked)
                if old_state != is_checked:
                    changed_count += 1
                    
        print(f"DEBUG: Changed {changed_count} items")  # 디버그
        
        # UI 상태 업데이트 (체크박스 시그널 차단하여 무한루프 방지)
        self.select_all_checkbox.blockSignals(True)
        self.update_ui_state()
        self.select_all_checkbox.blockSignals(False)
        
        # 로그 메시지 (전체 선택만 로그에 표시)
        action = "선택" if is_checked else "선택 해제"
        self.add_log(f"모든 파일 {action}됨")
        
    @pyqtSlot(QListWidgetItem)
    def on_item_clicked(self, item):
        """리스트 아이템 클릭 시 선택 상태 토글 (로그 없음)"""
        # 업데이트 중이면 선택 변경 불가
        if self.is_updating:
            return
            
        if item:
            item.toggle_selection()
            # 체크박스 시그널 차단하고 UI 업데이트
            self.select_all_checkbox.blockSignals(True)
            self.update_ui_state()
            self.select_all_checkbox.blockSignals(False)
        
    def get_selected_files(self):
        """선택된 항목의 파일 경로 리스트를 반환"""
        selected_files = []
        for i in range(self.wim_list.count()):
            item = self.wim_list.item(i)
            if item and item.is_selected:
                selected_files.append(item.file_path)
        return selected_files
        
    @pyqtSlot()
    def start_update_process(self):
        """업데이트 프로세스 시작"""
        selected_files = self.get_selected_files()
        
        if not selected_files:
            self.add_log("업데이트할 WIM 파일을 선택해주세요.")
            return
            
        self.add_log(f"{len(selected_files)}개 파일의 업데이트를 시작합니다...")
        
        # 선택된 파일 목록 로그
        for file_path in selected_files:
            filename = os.path.basename(file_path)
            self.add_log(f"   {filename}")
        
        # 업데이트 상태로 변경
        self.is_updating = True
        self.set_update_mode(True)
        
        # 시그널 발생
        self.start_update.emit(selected_files)
    
    @pyqtSlot()
    def cancel_update_process(self):
        """업데이트 프로세스 취소"""
        if self.is_updating:
            self.add_log("업데이트를 취소합니다...")
            
            # 취소 시그널 발생
            self.cancel_update.emit()
            
            # 즉시 UI 초기화
            self.reset_ui_immediately()
        
    def set_update_mode(self, updating):
        """업데이트 모드 UI 설정"""
        # 버튼 상태
        self.start_btn.setEnabled(not updating)
        self.cancel_btn.setEnabled(updating)
        
        # 폴더 선택 버튼
        self.folder_btn.setEnabled(not updating)
        
        # 전체 선택 체크박스
        self.select_all_checkbox.setEnabled(not updating)
        
        if updating:
            self.status_label.setText("업데이트 진행 중...")
        
    def reset_ui_immediately(self):
        """즉시 UI 초기화 (취소 시 사용)"""
        self.is_updating = False
        
        # 버튼 상태 초기화
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        # 컨트롤 다시 활성화
        self.folder_btn.setEnabled(True)
        self.select_all_checkbox.setEnabled(True)
        
        # 진행률 초기화
        self.progress_bar.setValue(0)
        self.status_label.setText("업데이트가 취소되었습니다.")
        
        # UI 상태 업데이트
        self.update_ui_state()
        
        self.add_log("업데이트가 취소되었습니다.")
        
    def update_ui_state(self):
        """UI 상태 업데이트 - 완전 수정 버전"""
        total_count = self.wim_list.count()
        selected_count = len(self.get_selected_files())
        
        print(f"DEBUG: update_ui_state - total={total_count}, selected={selected_count}")  # 디버그
        
        # 업데이트 중이 아닐 때만 시작 버튼 활성화
        if not self.is_updating:
            self.start_btn.setEnabled(selected_count > 0)
        
        # 선택 상태 라벨 업데이트
        self.selection_status_label.setText(f"선택: {selected_count}/{total_count}개")
        
        # 전체 선택 체크박스 상태 업데이트 (업데이트 중이 아닐 때만)
        if not self.is_updating:
            if total_count == 0:
                # 파일이 없으면 체크박스 비활성화
                self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
                self.select_all_checkbox.setEnabled(False)
                print("DEBUG: No files - checkbox disabled")
            elif selected_count == 0:
                # 아무것도 선택되지 않았으면 체크박스 해제 상태
                self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
                self.select_all_checkbox.setEnabled(True)
                print("DEBUG: Nothing selected - checkbox unchecked but enabled")
            elif selected_count == total_count:
                # 모두 선택되었으면 체크박스 선택 상태
                self.select_all_checkbox.setCheckState(Qt.CheckState.Checked)
                self.select_all_checkbox.setEnabled(True)
                print("DEBUG: All selected - checkbox checked")
            else:
                # 일부만 선택되었으면 중간 상태
                self.select_all_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
                self.select_all_checkbox.setEnabled(True)
                print("DEBUG: Partial selection - checkbox partially checked")
            
    def add_log(self, message):
        """로그 메시지 추가"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.appendPlainText(f"[{timestamp}] {message}")
        
        # 스크롤을 맨 아래로
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def update_progress(self, value, message=""):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)
            self.add_log(message)
            
    def reset_ui_after_completion(self):
        """작업 완료 후 UI 리셋"""
        self.is_updating = False
        
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        # 컨트롤 다시 활성화
        self.folder_btn.setEnabled(True)
        self.select_all_checkbox.setEnabled(True)
        
        self.progress_bar.setValue(100)
        self.status_label.setText("업데이트 완료")
        
        # UI 상태 업데이트
        self.update_ui_state()
