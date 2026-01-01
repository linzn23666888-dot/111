"""
Windows端主程序 - BeepBeep完整实现
"""

import sys
import time
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QTextEdit, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from config import *
from audio_utils import AudioHandler
from beepbeep_processor import BeepBeepProcessor
from network_comm import NetworkServer


class BeepBeepWindow(QMainWindow):
    """Windows端BeepBeep主窗口"""
    
    # 信号
    update_log_signal = pyqtSignal(str)
    update_distance_signal = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        
        # 初始化组件
        self.audio_handler = AudioHandler()
        self.processor = BeepBeepProcessor()
        self.network_server = NetworkServer()
        
        # 生成参考信号
        self.signal_A = self.audio_handler.generate_signal_A()  # 18kHz
        self.signal_B = self.audio_handler.generate_signal_B()  # 19kHz
        
        # 测距数据
        self.timestamps_A = None  # Windows端的时间戳 {tA1, tA3}
        self.timestamps_B = None  # Android端的时间戳 {tB1, tB3}
        self.recorded_audio = None  # 录音数据
        
        # 设置界面
        self.init_ui()
        
        # 连接信号
        self.update_log_signal.connect(self.log)
        self.update_distance_signal.connect(self.update_distance)
        
        # 启动网络服务器
        self.start_network_server()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("🎯 BeepBeep测距 - Windows端")
        self.setGeometry(100, 100, 600, 550)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("📡 BeepBeep双向测距系统")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 网络状态
        self.network_status = QLabel("🌐 网络: 初始化中...")
        self.network_status.setFont(QFont("Arial", 10))
        layout.addWidget(self.network_status)
        
        # 距离显示
        self.distance_label = QLabel("距离: -- 米")
        self.distance_label.setFont(QFont("Arial", 32, QFont.Bold))
        self.distance_label.setAlignment(Qt.AlignCenter)
        self.distance_label.setStyleSheet(
            "color: blue; padding: 30px; background-color: #f0f0f0; border-radius: 10px;"
        )
        layout.addWidget(self.distance_label)
        
        # 时间戳显示
        time_layout = QVBoxLayout()
        self.time_label_A = QLabel("Windows: tA1=--  tA3=--")
        self.time_label_B = QLabel("Android: tB1=--  tB3=--")
        time_layout.addWidget(self.time_label_A)
        time_layout.addWidget(self.time_label_B)
        layout.addLayout(time_layout)
        
        # 按钮
        self.start_btn = QPushButton("🚀 开始BeepBeep测距")
        self.start_btn.setFont(QFont("Arial", 12))
        self.start_btn.setMinimumHeight(50)
        self.start_btn.clicked.connect(self.start_beepbeep_ranging)
        layout.addWidget(self.start_btn)
        
        # 日志
        log_label = QLabel("📋 详细日志:")
        log_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        central_widget.setLayout(layout)
        
        self.log("="*60)
        self.log("BeepBeep双向测距系统")
        self.log(f"Windows频率: {SIGNAL_FREQUENCY_A}Hz | Android频率: {SIGNAL_FREQUENCY_B}Hz")
        self.log(f"声速: {SOUND_SPEED}m/s")
        self.log("="*60)
    
    def start_network_server(self):
        """启动网络服务器"""
        self.log("🌐 启动网络服务器...")
        
        if self.network_server.start_server(callback=self.on_receive_data):
            ip = self.network_server.get_local_ip()
            self.network_status.setText(f"🌐 等待连接 | IP: {ip}:{WIFI_PORT}")
            self.log(f"✅ 服务器启动: {ip}:{WIFI_PORT}")
            
            # 定时检查连接
            self.connection_timer = QTimer()
            self.connection_timer.timeout.connect(self.check_connection)
            self.connection_timer.start(1000)
        else:
            self.log("❌ 服务器启动失败")
    
    def check_connection(self):
        """检查连接状态"""
        if self.network_server.is_connected():
            ip = self.network_server.get_local_ip()
            self.network_status.setText(f"🌐 已连接 ✓ | IP: {ip}:{WIFI_PORT}")
        else:
            ip = self.network_server.get_local_ip()
            self.network_status.setText(f"🌐 等待连接 | IP: {ip}:{WIFI_PORT}")
    
    def on_receive_data(self, data):
        """接收Android端数据"""
        self.update_log_signal.emit(f"📥 收到: {data.get('type', 'unknown')}")
        
        msg_type = data.get('type', '')
        
        if msg_type == 'ready':
            self.update_log_signal.emit("✅ Android端已就绪")
        
        elif msg_type == 'timestamps':
            # 接收Android端的时间戳
            self.timestamps_B = {
                'tB1': data.get('tB1'),
                'tB3': data.get('tB3')
            }
            
            self.update_log_signal.emit(f"✅ 收到Android时间戳:")
            self.update_log_signal.emit(f"   tB1 = {self.timestamps_B['tB1']:.4f}秒")
            self.update_log_signal.emit(f"   tB3 = {self.timestamps_B['tB3']:.4f}秒")
            
            # 更新UI
            self.time_label_B.setText(
                f"Android: tB1={self.timestamps_B['tB1']:.4f}s  tB3={self.timestamps_B['tB3']:.4f}s"
            )
            
            # 如果Windows端也有时间戳，计算距离
            if self.timestamps_A:
                self.calculate_final_distance()
    
    def start_beepbeep_ranging(self):
        """开始BeepBeep测距"""
        if not self.network_server.is_connected():
            self.log("⚠️ 请先连接Android设备！")
            return
        
        self.log("\n" + "="*60)
        self.log("🚀 开始BeepBeep双向测距")
        self.log("="*60)
        
        self.start_btn.setEnabled(False)
        
        # 重置数据
        self.timestamps_A = None
        self.timestamps_B = None
        
        # 在新线程中执行测距
        threading.Thread(target=self._ranging_thread, daemon=True).start()
    
    def _ranging_thread(self):
        """测距线程"""
        try:
            # 1. 通知Android准备开始
            self.update_log_signal.emit("📤 通知Android准备...")
            self.network_server.send_data({
                'type': 'start_beepbeep',
                'message': 'Windows端开始BeepBeep测距'
            })
            
            time.sleep(0.5)  # 等待Android准备
            
            # 2. 开始录音（在发送信号前）
            self.update_log_signal.emit(f"🎤 开始录音 {RECORDING_DURATION}秒...")
            
            recorded_data = []
            
            def record_thread():
                recorded_data.append(
                    self.audio_handler.record_audio(RECORDING_DURATION)
                )
            
            rec_thread = threading.Thread(target=record_thread)
            rec_thread.start()
            
            time.sleep(0.3)  # 等待录音稳定
            
            # 3. 发送18kHz信号
            self.update_log_signal.emit("🔊 Windows发送18kHz信号...")
            self.audio_handler.play_signal(self.signal_A)
            
            # 4. 等待录音完成
            rec_thread.join()
            self.recorded_audio = recorded_data[0]
            
            self.update_log_signal.emit(f"✅ 录音完成: {len(self.recorded_audio)}采样点")
            
            # 5. 分析录音，提取时间戳
            self.update_log_signal.emit("📊 分析信号，提取时间戳...")
            
            timestamps = self.processor.extract_timestamps(
                self.recorded_audio,
                self.signal_A,
                self.signal_B,
                device_role='A'  # Windows端
            )
            
            if timestamps:
                self.timestamps_A = timestamps
                
                self.update_log_signal.emit(f"✅ Windows时间戳提取成功:")
                self.update_log_signal.emit(f"   tA1 = {timestamps['tA1']:.4f}秒")
                self.update_log_signal.emit(f"   tA3 = {timestamps['tA3']:.4f}秒")
                
                # 更新UI
                self.time_label_A.setText(
                    f"Windows: tA1={timestamps['tA1']:.4f}s  tA3={timestamps['tA3']:.4f}s"
                )
                
                # 6. 发送时间戳给Android
                self.network_server.send_data({
                    'type': 'timestamps',
                    'tA1': timestamps['tA1'],
                    'tA3': timestamps['tA3']
                })
                
                self.update_log_signal.emit("📤 已发送时间戳给Android")
                self.update_log_signal.emit("⏳ 等待Android数据...")
            else:
                self.update_log_signal.emit("❌ 时间戳提取失败！")
                self.update_log_signal.emit("💡 请检查：")
                self.update_log_signal.emit("   1. 两设备是否足够近(<5米)")
                self.update_log_signal.emit("   2. 环境是否安静")
                self.update_log_signal.emit("   3. 扬声器/麦克风是否正常")
            
        except Exception as e:
            self.update_log_signal.emit(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.start_btn.setEnabled(True)
    
    def calculate_final_distance(self):
        """计算最终距离"""
        if not self.timestamps_A or not self.timestamps_B:
            return
        
        self.log("\n" + "="*60)
        self.log("📐 计算最终距离...")
        
        try:
            distance = self.processor.calculate_distance_beepbeep(
                self.timestamps_A['tA1'],
                self.timestamps_A['tA3'],
                self.timestamps_B['tB1'],
                self.timestamps_B['tB3']
            )
            
            # 更新显示
            self.update_distance_signal.emit(distance)
            
            # 发送结果给Android
            self.network_server.send_data({
                'type': 'result',
                'distance': distance
            })
            
            self.log("="*60 + "\n")
            
        except Exception as e:
            self.log(f"❌ 距离计算失败: {e}")
    
    def update_distance(self, distance):
        """更新距离显示"""
        self.distance_label.setText(f"距离: {distance:.2f} 米")
    
    def log(self, message):
        """写入日志"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def closeEvent(self, event):
        """关闭窗口"""
        self.log("👋 关闭程序...")
        
        if hasattr(self, 'connection_timer'):
            self.connection_timer.stop()
        
        self.network_server.stop_server()
        self.audio_handler.close()
        
        event.accept()


# ========== 主程序 ==========
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BeepBeepWindow()
    window.show()
    sys.exit(app.exec_())