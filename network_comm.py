"""
网络通信模块 - 使用Socket实现WiFi通信
"""

import socket
import json
import threading
from config import *

class NetworkServer:
    """网络服务器类 - Windows端使用"""
    
    def __init__(self, port=WIFI_PORT):
        """
        初始化服务器
        
        参数:
            port: 监听端口号
        """
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.is_running = False
        self.receive_callback = None
        
        print(f"🌐 网络服务器初始化，端口: {port}")
    
    def get_local_ip(self):
        """
        获取本机局域网IP地址
        
        返回:
            str: IP地址
        """
        try:
            # 创建一个UDP socket连接到外部地址（不会真正发送数据）
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print(f"❌ 获取IP失败: {e}")
            return "127.0.0.1"
    
    def start_server(self, callback=None):
        """
        启动服务器，监听连接
        
        参数:
            callback: 接收到数据时的回调函数
        """
        self.receive_callback = callback
        
        try:
            # 创建socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # 允许地址重用（避免"地址已被使用"错误）
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 绑定地址和端口
            self.server_socket.bind(('0.0.0.0', self.port))
            
            # 开始监听（最多1个连接）
            self.server_socket.listen(1)
            
            self.is_running = True
            
            # 获取本机IP
            local_ip = self.get_local_ip()
            print(f"✅ 服务器启动成功！")
            print(f"📡 本机IP: {local_ip}")
            print(f"🔌 端口: {self.port}")
            print(f"📱 Android端请连接: {local_ip}:{self.port}")
            print(f"⏳ 等待Android设备连接...")
            
            # 在新线程中等待连接
            threading.Thread(target=self._accept_client, daemon=True).start()
            
            return True
            
        except Exception as e:
            print(f"❌ 服务器启动失败: {e}")
            return False
    
    def _accept_client(self):
        """在后台线程中接受客户端连接"""
        try:
            # 阻塞等待客户端连接
            self.client_socket, self.client_address = self.server_socket.accept()
            print(f"✅ Android设备已连接: {self.client_address}")
            
            # 开始接收数据
            self._receive_loop()
            
        except Exception as e:
            if self.is_running:
                print(f"❌ 连接错误: {e}")
    
    def _receive_loop(self):
        """持续接收数据"""
        while self.is_running and self.client_socket:
            try:
                # 接收数据
                data = self.client_socket.recv(BUFFER_SIZE)
                
                if not data:
                    print("⚠️  Android设备断开连接")
                    break
                
                # 解析JSON数据
                message = data.decode('utf-8')
                data_dict = json.loads(message)
                
                print(f"📥 收到数据: {data_dict}")
                
                # 调用回调函数
                if self.receive_callback:
                    self.receive_callback(data_dict)
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析错误: {e}")
            except Exception as e:
                print(f"❌ 接收数据错误: {e}")
                break
    
    def send_data(self, data_dict):
        """
        发送数据给Android端
        
        参数:
            data_dict: 要发送的字典数据
        
        返回:
            bool: 是否发送成功
        """
        if not self.client_socket:
            print("❌ 没有连接的设备")
            return False
        
        try:
            # 转换为JSON字符串
            message = json.dumps(data_dict)
            
            # 发送数据
            self.client_socket.sendall(message.encode('utf-8'))
            
            print(f"📤 发送数据: {data_dict}")
            return True
            
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            return False
    
    def is_connected(self):
        """检查是否有设备连接"""
        return self.client_socket is not None
    
    def stop_server(self):
        """停止服务器"""
        self.is_running = False
        
        try:
            if self.client_socket:
                self.client_socket.close()
                print("🔌 关闭客户端连接")
            
            if self.server_socket:
                self.server_socket.close()
                print("🔌 关闭服务器")
                
        except Exception as e:
            print(f"❌ 关闭错误: {e}")


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("="*60)
    print("🧪 网络服务器测试")
    print("="*60)
    
    def on_receive_data(data):
        """接收数据的回调函数"""
        print(f"\n🎉 回调函数收到数据: {data}")
        
        # 自动回复
        if server.is_connected():
            reply = {"type": "reply", "message": "收到你的数据了！"}
            server.send_data(reply)
    
    # 创建服务器
    server = NetworkServer()
    
    # 启动服务器
    if server.start_server(callback=on_receive_data):
        print("\n📱 现在你可以：")
        print("   1. 用Android设备连接到上面显示的IP和端口")
        print("   2. 或者在另一个终端运行测试客户端")
        print("   3. 输入 'quit' 退出\n")
        
        # 等待用户输入
        while True:
            cmd = input(">>> ")
            
            if cmd.lower() == 'quit':
                break
            elif cmd.lower() == 'send':
                # 测试发送
                if server.is_connected():
                    test_data = {"type": "test", "value": 123}
                    server.send_data(test_data)
                else:
                    print("⚠️  没有连接的设备")
            else:
                print("命令: send (发送测试数据) | quit (退出)")
    
    # 关闭服务器
    server.stop_server()
    print("\n👋 测试结束")