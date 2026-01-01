"""
音频工具 - 支持双频率BeepBeep
"""

import numpy as np
import pyaudio
import wave
from config import *


class AudioHandler:
    """音频处理类 - 支持双频率信号"""
    
    def __init__(self):
        """初始化音频处理器"""
        self.sample_rate = SAMPLE_RATE
        self.pyaudio_instance = pyaudio.PyAudio()
        
        # 音频格式
        self.format = pyaudio.paInt16
        self.channels = 1
        self.chunk_size = 1024
        
        print(f"🔊 音频系统初始化完成")
        print(f"   采样率: {self.sample_rate} Hz")
        print(f"   Windows频率: {SIGNAL_FREQUENCY_A} Hz")
        print(f"   Android频率: {SIGNAL_FREQUENCY_B} Hz")
    
    def generate_signal(self, frequency, duration=None, amplitude=None):
        """
        生成指定频率的正弦波信号
        
        参数:
            frequency: 信号频率 (Hz)
            duration: 持续时间 (秒)，默认使用配置值
            amplitude: 振幅 (0-1)，默认使用配置值
        
        返回:
            numpy.ndarray: 音频信号数组
        """
        if duration is None:
            duration = SIGNAL_DURATION
        if amplitude is None:
            amplitude = SIGNAL_AMPLITUDE
        
        # 生成时间轴
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        
        # 生成正弦波
        signal = amplitude * np.sin(2 * np.pi * frequency * t)
        
        # 添加渐入渐出，避免突然的咔哒声
        fade_samples = int(0.01 * self.sample_rate)  # 10ms渐变
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        
        signal[:fade_samples] *= fade_in
        signal[-fade_samples:] *= fade_out
        
        # 转换为16位整数
        signal_int = (signal * 32767).astype(np.int16)
        
        if DEBUG_MODE:
            print(f"   生成信号: {frequency}Hz, {duration:.2f}秒, {len(signal_int)}采样点")
        
        return signal_int
    
    def generate_signal_A(self):
        """生成Windows端信号（18kHz）"""
        return self.generate_signal(SIGNAL_FREQUENCY_A)
    
    def generate_signal_B(self):
        """生成Android端信号（19kHz）"""
        return self.generate_signal(SIGNAL_FREQUENCY_B)
    
    def play_signal(self, signal_data):
        """
        播放音频信号
        
        参数:
            signal_data: 音频数据数组
        """
        try:
            # 打开音频流
            stream = self.pyaudio_instance.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                output=True
            )
            
            # 播放
            stream.write(signal_data.tobytes())
            
            # 关闭流
            stream.stop_stream()
            stream.close()
            
            if DEBUG_MODE:
                print(f"   ✅ 播放完成")
            
        except Exception as e:
            print(f"   ❌ 播放失败: {e}")
    
    def record_audio(self, duration):
        """
        录制音频
        
        参数:
            duration: 录音时长 (秒)
        
        返回:
            numpy.ndarray: 录制的音频数据
        """
        try:
            # 打开录音流
            stream = self.pyaudio_instance.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            if DEBUG_MODE:
                print(f"   🎤 开始录音 {duration:.1f}秒...")
            
            # 录音
            frames = []
            num_chunks = int(self.sample_rate * duration / self.chunk_size)
            
            for _ in range(num_chunks):
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
            
            # 关闭流
            stream.stop_stream()
            stream.close()
            
            # 转换为numpy数组
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            
            if DEBUG_MODE:
                print(f"   ✅ 录音完成，{len(audio_data)}采样点")
            
            return audio_data
            
        except Exception as e:
            print(f"   ❌ 录音失败: {e}")
            return np.zeros(int(self.sample_rate * duration), dtype=np.int16)
    
    def save_audio(self, filename, audio_data):
        """
        保存音频到文件（用于调试）
        
        参数:
            filename: 文件名
            audio_data: 音频数据
        """
        if not SAVE_AUDIO:
            return
        
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.pyaudio_instance.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data.tobytes())
            
            print(f"   💾 音频已保存: {filename}")
        except Exception as e:
            print(f"   ⚠️ 保存音频失败: {e}")
    
    def close(self):
        """关闭音频系统"""
        self.pyaudio_instance.terminate()
        print("🔇 音频系统已关闭")


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("="*60)
    print("音频工具测试 - 双频率信号")
    print("="*60)
    
    handler = AudioHandler()
    
    # 测试生成两种频率的信号
    print("\n测试1: 生成并播放Windows信号 (18kHz)")
    signal_a = handler.generate_signal_A()
    print(f"信号长度: {len(signal_a)} 采样点")
    handler.play_signal(signal_a)
    
    import time
    time.sleep(1)
    
    print("\n测试2: 生成并播放Android信号 (19kHz)")
    signal_b = handler.generate_signal_B()
    print(f"信号长度: {len(signal_b)} 采样点")
    handler.play_signal(signal_b)
    
    print("\n测试3: 录音测试")
    recorded = handler.record_audio(2.0)
    print(f"录音长度: {len(recorded)} 采样点")
    
    handler.close()
    print("\n✅ 测试完成")