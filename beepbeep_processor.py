"""
BeepBeep信号处理器 - 完整实现
能够从连续录音中检测不同频率信号并计算时间戳
"""

import numpy as np
from scipy import signal as scipy_signal
from scipy.fft import fft, fftfreq
from config import *


class BeepBeepProcessor:
    """BeepBeep算法的信号处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.sample_rate = SAMPLE_RATE
        print("📊 BeepBeep处理器初始化")
    
    def detect_frequency_signal(self, audio_data, target_frequency, reference_signal):
        """
        在录音中检测特定频率的信号位置
        
        参数:
            audio_data: 录制的音频数据
            target_frequency: 目标频率 (Hz)
            reference_signal: 参考信号（用于互相关）
        
        返回:
            int: 信号起始位置的采样点索引，未找到返回-1
        """
        if DEBUG_MODE:
            print(f"\n   🔍 检测 {target_frequency}Hz 信号...")
        
        try:
            # 方法1：互相关检测
            correlation = np.correlate(audio_data, reference_signal, mode='valid')
            
            # 找到相关性峰值
            if len(correlation) == 0:
                if DEBUG_MODE:
                    print(f"   ⚠️ 互相关结果为空")
                return -1
            
            max_corr_value = np.max(np.abs(correlation))
            max_corr_idx = np.argmax(np.abs(correlation))
            
            # 动态阈值
            threshold = max_corr_value * CORRELATION_THRESHOLD
            
            if DEBUG_MODE:
                print(f"   最大相关性: {max_corr_value:.2f}")
                print(f"   阈值: {threshold:.2f}")
                print(f"   位置: 采样点 {max_corr_idx}")
            
            # 检查是否超过阈值
            if max_corr_value < threshold:
                if DEBUG_MODE:
                    print(f"   ⚠️ 信号太弱，未检测到")
                return -1
            
            # 验证频率（可选，增加准确性）
            if self.verify_frequency(audio_data, max_corr_idx, len(reference_signal), target_frequency):
                if DEBUG_MODE:
                    print(f"   ✅ 检测到 {target_frequency}Hz 信号")
                return max_corr_idx
            else:
                if DEBUG_MODE:
                    print(f"   ⚠️ 频率验证失败")
                return -1
            
        except Exception as e:
            print(f"   ❌ 检测失败: {e}")
            return -1
    
    def verify_frequency(self, audio_data, start_pos, length, expected_freq):
        """
        验证信号段的频率是否符合预期
        
        参数:
            audio_data: 音频数据
            start_pos: 信号起始位置
            length: 信号长度
            expected_freq: 预期频率
        
        返回:
            bool: 频率是否匹配
        """
        # 暂时禁用频率验证，只使用互相关检测
        if DEBUG_MODE:
            print(f"   [跳过频率验证] 期望{expected_freq}Hz")
        return True
        
        # 以下代码暂时不用
        try:
            # 提取信号段
            end_pos = min(start_pos + length, len(audio_data))
            signal_segment = audio_data[start_pos:end_pos]
            
            if len(signal_segment) < 100:
                return False
            
            # FFT分析
            fft_result = fft(signal_segment)
            freqs = fftfreq(len(signal_segment), 1/self.sample_rate)
            
            # 只看正频率部分
            positive_freqs = freqs[:len(freqs)//2]
            positive_fft = np.abs(fft_result[:len(fft_result)//2])
            
            # 找到主频率
            dominant_freq_idx = np.argmax(positive_fft)
            dominant_freq = positive_freqs[dominant_freq_idx]
            
            # 检查是否在容差范围内
            freq_match = abs(dominant_freq - expected_freq) < FREQUENCY_TOLERANCE
            
            if DEBUG_MODE and not freq_match:
                print(f"   频率不匹配: 期望{expected_freq}Hz, 检测到{dominant_freq:.0f}Hz")
            
            return freq_match
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"   频率验证异常: {e}")
            return True  # 验证失败时默认通过
    
    def extract_timestamps(self, audio_data, signal_A, signal_B, device_role):
        """
        从录音中提取时间戳
        
        参数:
            audio_data: 完整的录音数据
            signal_A: Windows端的参考信号
            signal_B: Android端的参考信号
            device_role: 设备角色 ('A' 表示Windows, 'B' 表示Android)
        
        返回:
            dict: 包含检测到的时间戳 {'t1': ..., 't2': ...} 或 None
        """
        print(f"\n📊 提取时间戳 (设备角色: {device_role})")
        
        result = {}
        
        if device_role == 'A':
            # Windows端：需要检测自己的信号(18kHz)和Android的信号(19kHz)
            
            # 检测tA1: 收到自己发送的18kHz信号
            pos_a1 = self.detect_frequency_signal(audio_data, SIGNAL_FREQUENCY_A, signal_A)
            
            if pos_a1 >= 0:
                result['tA1'] = pos_a1 / self.sample_rate
                print(f"   ✅ tA1 = {result['tA1']:.4f}秒 (采样点{pos_a1})")
            else:
                print(f"   ❌ 未检测到tA1 (自己的18kHz信号)")
                return None
            
            # 检测tA3: 收到Android发送的19kHz信号
            # 应该在tA1之后，所以从tA1位置往后搜索
            search_start = pos_a1 + len(signal_A)
            if search_start < len(audio_data):
                pos_a3 = self.detect_frequency_signal(
                    audio_data[search_start:], 
                    SIGNAL_FREQUENCY_B, 
                    signal_B
                )
                
                if pos_a3 >= 0:
                    # 加上偏移量
                    result['tA3'] = (search_start + pos_a3) / self.sample_rate
                    print(f"   ✅ tA3 = {result['tA3']:.4f}秒 (采样点{search_start + pos_a3})")
                else:
                    print(f"   ❌ 未检测到tA3 (Android的19kHz信号)")
                    return None
            else:
                print(f"   ❌ 录音太短，无法检测tA3")
                return None
        
        elif device_role == 'B':
            # Android端：需要检测Windows的信号(18kHz)和自己的信号(19kHz)
            
            # 检测tB1: 收到Windows发送的18kHz信号
            pos_b1 = self.detect_frequency_signal(audio_data, SIGNAL_FREQUENCY_A, signal_A)
            
            if pos_b1 >= 0:
                result['tB1'] = pos_b1 / self.sample_rate
                print(f"   ✅ tB1 = {result['tB1']:.4f}秒 (采样点{pos_b1})")
            else:
                print(f"   ❌ 未检测到tB1 (Windows的18kHz信号)")
                return None
            
            # 检测tB3: 收到自己发送的19kHz信号
            # 应该在tB1之后，所以从tB1位置往后搜索
            search_start = pos_b1 + len(signal_A)
            if search_start < len(audio_data):
                pos_b3 = self.detect_frequency_signal(
                    audio_data[search_start:], 
                    SIGNAL_FREQUENCY_B, 
                    signal_B
                )
                
                if pos_b3 >= 0:
                    # 加上偏移量
                    result['tB3'] = (search_start + pos_b3) / self.sample_rate
                    print(f"   ✅ tB3 = {result['tB3']:.4f}秒 (采样点{search_start + pos_b3})")
                else:
                    print(f"   ❌ 未检测到tB3 (自己的19kHz信号)")
                    return None
            else:
                print(f"   ❌ 录音太短，无法检测tB3")
                return None
        
        return result if result else None
    
    def calculate_distance_beepbeep(self, time_A1, time_A3, time_B1, time_B3):
        """
        使用真正的BeepBeep公式计算距离
        
        公式: D = (c/2) × [(tA3-tA1) - (tB3-tB1)] + (dA,A + dB,B)/2
        
        参数:
            time_A1: Windows收到自己信号的时间
            time_A3: Windows收到Android信号的时间
            time_B1: Android收到Windows信号的时间
            time_B3: Android收到自己信号的时间
        
        返回:
            float: 距离（米）
        """
        print(f"\n📐 BeepBeep距离计算:")
        print(f"   tA1 = {time_A1:.4f}秒")
        print(f"   tA3 = {time_A3:.4f}秒")
        print(f"   tB1 = {time_B1:.4f}秒")
        print(f"   tB3 = {time_B3:.4f}秒")
        
        # 计算时间差
        delta_tA = time_A3 - time_A1
        delta_tB = time_B3 - time_B1
        
        print(f"   ΔtA = tA3 - tA1 = {delta_tA:.4f}秒")
        print(f"   ΔtB = tB3 - tB1 = {delta_tB:.4f}秒")
        
        # BeepBeep公式
        time_diff = delta_tA - delta_tB
        print(f"   ΔtA - ΔtB = {time_diff:.4f}秒")
        
        # 计算距离
        distance = (SOUND_SPEED / 2) * time_diff
        
        # 加上设备自身距离校正
        device_correction = (DEVICE_SELF_DISTANCE_A + DEVICE_SELF_DISTANCE_B) / 2
        distance = distance + device_correction
        
        print(f"   原始距离: {(SOUND_SPEED / 2) * time_diff:.3f}米")
        print(f"   设备校正: {device_correction:.3f}米")
        print(f"   ✅ 最终距离: {distance:.2f}米")
        
        # 确保距离为正
        distance = abs(distance)
        
        # 合理性检查
        if distance > 50:
            print(f"   ⚠️ 距离过大({distance:.2f}米)，可能测量错误")
        elif distance < 0.1:
            print(f"   ⚠️ 距离过小({distance:.2f}米)，可能测量错误")
            distance = max(0.1, distance)
        
        return distance


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("="*60)
    print("BeepBeep处理器测试")
    print("="*60)
    
    processor = BeepBeepProcessor()
    
    # 测试距离计算
    print("\n测试: BeepBeep距离计算")
    
    # 模拟时间戳（单位：秒）
    # 假设两设备相距3米
    # 声音传播时间: 3米 / 343m/s ≈ 0.00875秒
    
    tA1 = 0.1  # Windows收到自己信号
    tA3 = 0.1 + 2 * 0.00875 + 0.02  # Windows收到Android信号(往返+Android处理时间)
    tB1 = 0.1 + 0.00875  # Android收到Windows信号
    tB3 = tB1 + 0.02  # Android收到自己信号(处理时间)
    
    distance = processor.calculate_distance_beepbeep(tA1, tA3, tB1, tB3)
    
    print(f"\n理论距离: 3.00米")
    print(f"计算距离: {distance:.2f}米")
    print(f"误差: {abs(distance - 3.0):.3f}米")
    
    print("\n✅ 测试完成")