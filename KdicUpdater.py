import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from modules.view import View
from modules.worker import Worker
from modules.scanner import ScannerWorker

class MainController:
    def __init__(self):
        self.view = View()
        self.scanner = None  # Scanner 스레드
        self.updater = None  # Worker -> Updater로 이름 변경

        self.connect_signals()

    def connect_signals(self):
        """시그널 연결"""
        # View -> Controller
        self.view.folder_selected.connect(self.on_folder_selected)
        self.view.start_update.connect(self.on_start_update)
        self.view.cancel_update.connect(self.on_cancel_update)

    def on_folder_selected(self, folder_path):
        """View에서 폴더 선택 신호를 받았을 때"""
        # 기존 스캐너가 실행 중이면 중지 시도
        if self.scanner and self.scanner.isRunning():
            self.scanner.stop()
            self.scanner.wait() # 스레드가 완전히 종료될 때까지 대기

        self.scanner = ScannerWorker(folder_path)

        # Scanner -> View 시그널 연결
        self.scanner.scan_started.connect(lambda: self.view.set_scan_mode(True))
        self.scanner.scan_complete.connect(self.on_scan_completed)
        self.scanner.log_message.connect(self.view.add_log)

        # 스캐너가 종료되면 스스로 삭제되도록 설정
        self.scanner.finished.connect(self.scanner.deleteLater)
        self.scanner.start()

    def on_scan_completed(self, wim_info_list):
        """스캔 완료 시"""
        self.view.update_wim_list(wim_info_list)
        self.view.set_scan_mode(False)
        self.scanner = None

    def on_start_update(self, file_list):
        """View에서 업데이트 시작 신호를 받았을 때"""
        self.updater = Worker(file_list)  # Worker 스레드 생성

        # Updater -> View 시그널 연결
        self.updater.progress.connect(self.view.update_progress)
        self.updater.finished.connect(self.on_update_finished)
        self.updater.log_message.connect(self.view.add_log)

        self.updater.finished.connect(self.updater.deleteLater)
        self.updater.start()
        self.view.set_update_mode(True)

    def on_cancel_update(self):
        """View에서 업데이트 취소 신호를 받았을 때"""
        if self.updater and self.updater.isRunning():
            self.updater.stop()
            # self.view.add_log("사용자에 의해 업데이트가 중단되었습니다.") # worker에서 처리
            # self.view.reset_ui_immediately() # worker에서 처리

    def on_update_finished(self):
        """Updater 스레드 작업 완료 시"""
        if self.updater and self.updater.is_running: # 정상 종료 시에만
            self.view.add_log("모든 업데이트 작업이 완료되었습니다.")
            self.view.reset_ui_after_completion()
        else: # 사용자에 의해 중단된 경우
             self.view.add_log("사용자에 의해 업데이트가 중단되었습니다.")
             self.view.reset_ui_immediately()

        self.updater = None

    def show(self):
        """GUI 표시"""
        self.view.show()

def main():
    """메인 함수"""
    app = QApplication(sys.argv)

    # 애플리케이션 정보 설정
    app.setApplicationName("KdicUpdater")
    app.setApplicationDisplayName("Kdic WIM Updater")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Software")
    app.setOrganizationDomain("kdic.local")

    # 아이콘 설정
    icon_path = "icon/kdic.ico"
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        # 절대 경로로 다시 시도
        try:
            base_path = sys._MEIPASS # PyInstaller 임시 경로
        except Exception:
            base_path = os.path.abspath(".")

        icon_path = os.path.join(base_path, "icon", "kdic.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        else:
            print(f"⚠️ 아이콘 파일을 찾을 수 없습니다: {icon_path}")

    # 메인 컨트롤러 생성 및 실행
    controller = MainController()
    controller.show()

    return app.exec()

if __name__ == '__main__':
    sys.exit(main())