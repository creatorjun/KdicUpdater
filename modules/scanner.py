import os
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ScannerWorker(QThread):
    """지정된 폴더에서 WIM 파일을 스캔하고 정보를 추출하는 스레드"""
    scan_complete = pyqtSignal(list)  # 스캔 완료 시 파일 정보 리스트 전달
    log_message = pyqtSignal(str)     # 로그 메시지 전달
    scan_started = pyqtSignal()       # 스캔 시작 신호
    
    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.is_running = True

    def run(self):
        """스레드 실행 함수"""
        self.log_message.emit(f"'{self.folder_path}' 폴더에서 WIM 파일을 스캔합니다...")
        self.scan_started.emit()
        
        wim_files_info = []
        try:
            files = [f for f in os.listdir(self.folder_path) if f.lower().endswith('.wim')]
            if not files:
                self.log_message.emit("스캔할 WIM 파일이 없습니다.")
                self.scan_complete.emit([])
                return

            total_files = len(files)
            for i, file_name in enumerate(files):
                if not self.is_running:
                    self.log_message.emit("사용자에 의해 스캔이 중단되었습니다.")
                    break
                
                file_path = os.path.join(self.folder_path, file_name)
                self.log_message.emit(f"({i+1}/{total_files}) '{file_name}' 정보 조회 중...")
                
                try:
                    # DISM 명령 실행
                    cmd = f'dism /Get-WimInfo /WimFile:"{file_path}"'
                    
                    # 콘솔 창이 나타나지 않도록 startupinfo 설정
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    
                    result = subprocess.run(
                        cmd, 
                        shell=True, 
                        capture_output=True, 
                        text=True, 
                        encoding='utf-8',
                        startupinfo=startupinfo
                    )
                    
                    if result.returncode == 0:
                        # DISM 출력 결과 파싱
                        wim_info = self.parse_dism_output(result.stdout)
                        wim_info['file_path'] = file_path
                        wim_files_info.append(wim_info)
                    else:
                        self.log_message.emit(f"'{file_name}' 정보 조회 실패: {result.stderr}")
                        
                except Exception as e:
                    self.log_message.emit(f"'{file_name}' 처리 중 오류 발생: {str(e)}")

        except Exception as e:
            self.log_message.emit(f"폴더 스캔 중 오류 발생: {str(e)}")
            
        self.scan_complete.emit(wim_files_info)

    def parse_dism_output(self, output):
        """DISM /Get-WimInfo 결과 텍스트를 파싱하여 정보 추출"""
        info = {'name': 'N/A', 'version': 'N/A', 'build': 'N/A'}
        lines = output.splitlines()
        
        try:
            for i, line in enumerate(lines):
                # 보통 첫 번째 이미지의 정보를 사용
                if "인덱스 : 1" in line:
                    for sub_line in lines[i:]:
                        if '이름 :' in sub_line and info['name'] == 'N/A':
                            info['name'] = sub_line.split(':', 1)[1].strip()
                        elif '버전 :' in sub_line and info['version'] == 'N/A':
                            # 예: 버전 : 10.0.22631
                            version_str = sub_line.split(':', 1)[1].strip()
                            parts = version_str.split('.')
                            if len(parts) >= 3:
                                info['version'] = f"{parts[0]}.{parts[1]}"
                                info['build'] = parts[2]
                            break # 버전 정보 찾으면 종료
                    break # 인덱스 1 찾으면 종료
        except Exception:
            # 파싱 실패 시 기본값 반환
            pass
            
        return info

    def stop(self):
        """스레드 중지"""
        self.is_running = False