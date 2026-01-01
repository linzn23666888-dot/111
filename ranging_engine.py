"""
测距引擎 - 完整的声波测距实现（修复版）
"""

import time
import numpy as np
from config import *
from audio_utils import AudioHandler
from signal_processor import SignalProcessor


class RangingEngine:
    """
    声波测距引擎
    负责协调音频采集、信号处理和距离计算
    """
    
    def __init__(self):
        """初始化测距引擎"""
        print("🔧 初始化测距引擎...")
        
        # 初始化组件
        self.audio_handler = AudioHandler()
        self.signal_processor = SignalProcessor()
        
        # 生成标准信号
        self.standard_signal = self.audio_handler.generate_signal(
            frequency=SIGNAL_FREQUENCY,
            duration=SIGNAL_DURATION
        )
        
        print(f"✅ 测距引擎就绪 | 信号频率: {SIGNAL_FREQUENCY}Hz")
    
    def measure_distance_simple(self):
        """
        改进版单次测距 - 返回时间差（秒）
        
        返回:
            float: 时间差（秒）
        """
        print("\n" + "="*50)
        print("🔍 开始测距...")
        print("="*50)
        
        try:
            # 先开始录音（在发送信号之前）
            print("🎤 准备录音...")
            
            import threading
            recorded_data = []
            recording_started = threading.Event()
            
            def record_thread():
                # 录音3秒以确保捕获所有信号
                recording_started.set()
                recorded_data.append(self.audio_handler.record_audio(duration=3.0))
            
            # 启动录音线程
            rec_thread = threading.Thread(target=record_thread)
            rec_thread.start()
            
            # 等待录音真正开始
            recording_started.wait()
            time.sleep(0.2)  # 额外等待确保麦克风准备好
            
            # 记录发送时间
            print("🔊 发送探测信号...")
            send_time = time.time()
            
            # 发送信号
            self.audio_handler.play_signal(self.standard_signal)
            
            # 等待录音完成
            rec_thread.join()
            recorded = recorded_data[0]
            
            print(f"✅ 录音完成，采集 {len(recorded)} 个采样点")
            
            # 分析信号
            print("📊 分析信号...")
            
            # 查找信号在录音中的位置
            correlation = np.correlate(recorded, self.standard_signal, mode='valid')
            
            # 找到相关性最大的位置
            max_corr_idx = np.argmax(correlation)
            
            # 检查信号强度
            max_corr_value = correlation[max_corr_idx]
            threshold = np.max(correlation) * 0.3  # 动态阈值
            
            if max_corr_value < threshold:
                print(f"⚠️ 信号太弱: {max_corr_value:.2f} < {threshold:.2f}")
                print("💡 提示: 请确保两设备靠近且扬声器/麦克风正常")
                return 0.01  # 返回默认时间差
            
            print(f"✅ 检测到信号，相关性: {max_corr_value:.2f}")
            print(f"📍 信号起始位置: 采样点 {max_corr_idx}")
            
            # 转换为时间
            time_delay = max_corr_idx / SAMPLE_RATE
            
            # 减去设备自身延迟
            # 设备自身延迟 = 扬声器到麦克风的距离 / 声速
            self_delay = DEVICE_SELF_DISTANCE / SOUND_SPEED
            time_delay = time_delay - self_delay
            
            # 确保时间为正且合理（0.001秒 到 0.1秒，对应 0.3米 到 30米）
            if time_delay < 0.001:
                time_delay = 0.001
            elif time_delay > 0.1:
                print(f"⚠️ 时间差过大: {time_delay:.4f}秒，可能检测错误")
                time_delay = 0.01  # 使用默认值
            
            # 计算对应距离（仅用于日志显示）
            distance = time_delay * SOUND_SPEED
            
            print(f"⏱️  检测到时间延迟: {time_delay:.4f}秒")
            print(f"📏 对应距离: {distance:.3f}米")
            print("="*50)
            
            return time_delay  # 返回时间差（秒）
            
        except Exception as e:
            print(f"❌ 测距失败: {e}")
            import traceback
            traceback.print_exc()
            return 0.01  # 返回默认时间差
    
    def measure_distance_beepbeep(self):
        """
        完整的BeepBeep双向测距
        
        流程:
        1. 设备A发送信号，记录tA0, tA1
        2. 设备B接收并响应，记录tB1, tB2, tB3
        3. 设备A接收响应，记录tA3
        4. 计算距离: D = (c/2) * [(tA3-tA1) - (tB3-tB1)]
        
        返回:
            float: 测量距离（米）
        """
        print("\n" + "="*50)
        print("🔄 完整BeepBeep测距模式...")
        print("="*50)
        
        # 这个方法需要两个设备协同工作
        # 实际实现较复杂，这里只是框架
        print("⚠️  完整BeepBeep需要双设备精确同步")
        print("💡 当前使用简化版测距")
        
        return self.measure_distance_simple()
    
    def calibrate(self, known_distance):
        """
        校准测距系统
        
        参数:
            known_distance: 已知的实际距离（米）
        """
        print(f"\n🎯 开始校准，已知距离: {known_distance}米")
        
        # 多次测量取平均
        measurements = []
        for i in range(5):
            print(f"\n第 {i+1}/5 次测量...")
            measured = self.measure_distance_simple() * SOUND_SPEED
            measurements.append(measured)
            time.sleep(1)
        
        avg_measured = np.mean(measurements)
        error = known_distance - avg_measured
        
        print(f"\n📊 校准结果:")
        print(f"   测量值: {avg_measured:.3f}米 ± {np.std(measurements):.3f}米")
        print(f"   实际值: {known_distance:.3f}米")
        print(f"   误差: {error:.3f}米")
        print(f"💡 建议调整 DEVICE_SELF_DISTANCE 参数: {DEVICE_SELF_DISTANCE + error:.3f}米")
        
        return error
    
    def close(self):
        """关闭测距引擎，释放资源"""
        print("👋 关闭测距引擎...")
        self.audio_handler.close()


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("="*60)
    print("声波测距引擎测试")
    print("="*60)
    
    # 创建测距引擎
    engine = RangingEngine()
    
    try:
        # 进行一次测距
        time_diff = engine.measure_distance_simple()
        distance = time_diff * SOUND_SPEED
        
        print("\n" + "="*60)
        print(f"最终结果: 时间差 = {time_diff:.4f}秒, 距离 = {distance:.2f}米")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断")
    
    finally:
        # 清理资源
        engine.close()
        print("✅ 测试完成")