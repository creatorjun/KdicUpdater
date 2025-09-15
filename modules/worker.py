import time
import os
from PyQt6.QtCore import QThread, pyqtSignal

class Worker(QThread):
    """WIM 업데이트 작업을 수행하는 스레드"""
    progress = pyqtSignal(int, str)  # 진행률 (값, 메시지)
    finished = pyqtSignal()          # 작업 완료
    log_message = pyqtSignal(str)    # 로그 메시지

    def __init__(self, file_list):
        super().__init__()
        self.file_list = file_list
        self.is_running = True

    def run(self):
        """스레드 실행 함수"""
        total_files = len(self.file_list)
        for i, file_path in enumerate(self.file_list):
            if not self.is_running:
                break # 중지 신호가 오면 루프 종료

            file_name = os.path.basename(file_path)
            self.log_message.emit(f"'{file_name}' 업데이트 시작...")
            
            # TODO: 실제 WIM 업데이트 로직 구현
            # 예시로 5초간의 지연을 시뮬레이션합니다.
            for step in range(101):
                if not self.is_running:
                    break
                time.sleep(0.05) # 0.05초 * 100 = 5초
                
                # 진행률 업데이트 (전체 진행률 기준)
                overall_progress = int(((i + (step / 100)) / total_files) * 100)
                status_message = f"({i+1}/{total_files}) {file_name} 처리 중... {step}%"
                self.progress.emit(overall_progress, status_message)
            
            if self.is_running:
                self.log_message.emit(f"'{file_name}' 업데이트 완료.")

        self.finished.emit()

    def stop(self):
        """스레드 중지"""
        self.is_running = False