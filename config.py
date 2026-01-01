"""
配置文件 - BeepBeep完整实现版
"""

# ========== 音频参数 ==========
SAMPLE_RATE = 44100  # 采样率 (Hz)

# 双频率信号设计
SIGNAL_FREQUENCY_A = 18000  # Windows端使用的频率 (Hz)
SIGNAL_FREQUENCY_B = 19000  # Android端使用的频率 (Hz)

SIGNAL_DURATION = 0.3  # 信号持续时间 (秒) - 缩短以便快速响应
SIGNAL_AMPLITUDE = 0.8  # 信号幅度 (0-1)

# ========== 物理参数 ==========
SOUND_SPEED = 343.0  # 声速 (m/s) 常温下

# 设备自身距离（扬声器到麦克风）
DEVICE_SELF_DISTANCE_A = 0.08  # Windows设备 (米) - 笔记本约8cm
DEVICE_SELF_DISTANCE_B = 0.05  # Android设备 (米) - 手机约5cm

# ========== 信号检测参数 ==========
CORRELATION_THRESHOLD = 0.3  # 互相关阈值（相对于最大值的比例）
MIN_SIGNAL_STRENGTH = 100  # 最小信号强度

# 频率检测容差
FREQUENCY_TOLERANCE = 500  # Hz，允许±500Hz的频率偏差

# ========== 网络参数 ==========
WIFI_PORT = 5000  # WiFi通信端口

# ========== 测距参数 ==========
RECORDING_DURATION = 4.0  # 完整测距过程的录音时长（秒）
RESPONSE_DELAY = 0.5  # Android收到信号后等待多久发送响应（秒）

# ========== 调试参数 ==========
DEBUG_MODE = True  # 是否打印详细调试信息
SAVE_AUDIO = False  # 是否保存音频文件用于调试