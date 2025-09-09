import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from modules.view import View

class MainController:
    def __init__(self):
        self.view = View()
        self.connect_signals()
        
    def connect_signals(self):
        """시그널 연결"""
        self.view.folder_selected.connect(self.on_folder_selected)
        self.view.start_update.connect(self.on_start_update)
        
    def on_folder_selected(self, folder_path):
        """폴더 선택 시 처리"""
        print(f"Selected folder: {folder_path}")
        
    def on_start_update(self, file_list):
        """업데이트 시작 시 처리"""
        print(f"Starting update for {len(file_list)} files:")
        for file_path in file_list:
            print(f"  - {file_path}")
        
        # TODO: 실제 업데이트 로직 연결
        
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
    
    # 아이콘 설정 (상대 경로 및 절대 경로 모두 지원)
    icon_path = "icon/kdic.ico"
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        print(f"✅ 아이콘 로드 성공: {icon_path}")
    else:
        # 절대 경로로 다시 시도
        icon_path = os.path.join(os.path.dirname(__file__), "icon", "kdic.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            print(f"✅ 아이콘 로드 성공: {icon_path}")
        else:
            print(f"⚠️  아이콘 파일을 찾을 수 없습니다: {icon_path}")
    
    # 메인 컨트롤러 생성 및 실행
    controller = MainController()
    controller.show()
    
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())
