"""
信号处理类 - 负责信号分析和测距计算
"""

import numpy as np
from scipy import signal
from config import *

class SignalProcessor:
    """信号处理器"""
    
    def __init__(self):
        """初始化"""
        print("📊 信号处理器初始化")
    
    def find_signal_start(self, recorded_audio, sent_signal):
        """
        使用互相关找到信号起始位置
        
        参数:
            recorded_audio: 录制的音频 (numpy数组)
            sent_signal: 发送的信号 (numpy数组)
        
        返回:
            int: 信号起始位置的采样点索引
        """
        # 归一化信号 (防止幅度影响结果)
        recorded_norm = recorded_audio / np.max(np.abs(recorded_audio))
        sent_norm = sent_signal / np.max(np.abs(sent_signal))
        
        # 计算互相关
        correlation = signal.correlate(recorded_norm, sent_norm, mode='valid')
        
        # 找到最大相关值的位置
        peak_index = np.argmax(np.abs(correlation))
        
        print(f"📍 信号起始位置: 采样点 {peak_index}")
        return peak_index
    
    def samples_to_time(self, num_samples):
        """
        将采样点数转换为时间
        
        参数:
            num_samples: 采样点数
        
        返回:
            float: 时间 (秒)
        """
        return num_samples / SAMPLE_RATE
    
    def time_to_distance(self, time_diff):
        """
        根据时间差计算距离
        
        参数:
            time_diff: 时间差 (秒)
        
        返回:
            float: 距离 (米)
        """
        return SOUND_SPEED * time_diff
    
    def calculate_distance(self, time_diff_A, time_diff_B):
        """
        根据BeepBeep算法计算距离
        
        参数:
            time_diff_A: 设备A的时间差 (tA3 - tA1)
            time_diff_B: 设备B的时间差 (tB3 - tB1)
        
        返回:
            float: 两设备间距离 (米)
        """
        # 根据公式: D = c/2 * [(tA3-tA1) - (tB3-tB1)] + (dA,A + dB,B)/2
        distance = (SOUND_SPEED / 2) * (time_diff_A - time_diff_B) + DEVICE_SELF_DISTANCE
        
        print(f"📏 计算距离: {distance:.3f} 米")
        return distance


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=== 测试 SignalProcessor ===\n")
    
    processor = SignalProcessor()
    
    # 测试1: 采样点转时间
    samples = 44100  # 1秒的采样点数
    time = processor.samples_to_time(samples)
    print(f"测试1: {samples} 采样点 = {time} 秒")
    
    # 测试2: 时间转距离
    time_diff = 0.01  # 10毫秒
    distance = processor.time_to_distance(time_diff)
    print(f"测试2: {time_diff} 秒时间差 = {distance:.3f} 米")
    
    # 测试3: 计算距离
    # 假设 tA3-tA1 = 0.02秒, tB3-tB1 = 0.01秒
    final_distance = processor.calculate_distance(0.02, 0.01)
    print(f"测试3: 最终距离 = {final_distance:.3f} 米")
    
    print("\n✅ 所有测试完成！")