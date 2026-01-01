import pyaudio
import numpy as np

# 这个程序会录音3秒，然后播放出来

print("=== 音频设备测试程序 ===")
print("准备录音3秒...")

# 设置参数
CHUNK = 1024          # 每次读取的音频块大小
FORMAT = pyaudio.paInt16  # 音频格式
CHANNELS = 1          # 单声道
RATE = 44100          # 采样率 44.1kHz
RECORD_SECONDS = 3    # 录音时长

# 初始化PyAudio
p = pyaudio.PyAudio()

# 打开麦克风开始录音
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("🎤 开始录音...")
frames = []

# 录音3秒
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("✅ 录音完成！")

# 停止录音
stream.stop_stream()
stream.close()

# 播放刚才录的音
print("🔊 播放录音...")
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True)

for frame in frames:
    stream.write(frame)

print("✅ 播放完成！")

# 清理资源
stream.stop_stream()
stream.close()
p.terminate()

print("测试成功！你的麦克风和扬声器都正常工作！")