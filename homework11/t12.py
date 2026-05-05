import socket
import struct
import sys
from datetime import datetime

def ntp_server(port):
    # NTP 时间戳偏移量 (1900-01-01 到 1970-01-01 的秒数)
    NTP_DELTA = 2208988800

    # 创建 UDP 套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', port))
    print(f"NTP 服务器已启动，监听端口 {port}...")

    while True:
        try:
            # 接收客户端请求
            data, client_address = server_socket.recvfrom(1024)
            print(f"收到来自 {client_address} 的请求")

            # 解析 NTP 请求报文 (至少需要 48 字节)
            if len(data) < 48:
                continue

            # 解包 NTP 头部
            # !BBBBII4sQQQQ: 模式/版本/层/精度/根延迟/根离散/参考ID/参考时间/起源时间/接收时间/发送时间
            ntp_fields = struct.unpack('!BBBBII4sQQQQ', data[:48])
            
            # 构造 NTP 响应报文
            # 设置模式为 4 (服务器), 版本号通常保持不变
            mode_version = 0x24  # NTP Version 4, Mode 4 (Server)
            stratum = 1          # 一级服务器
            poll = ntp_fields[3] # 保持轮询间隔
            precision = 0        # 精度
            
            # 获取当前时间 (网络时间 = Unix时间 + NTP_DELTA)
            current_time = int(time.time() + NTP_DELTA)
            
            # 构造响应数据
            # 16 字节头部 + 48 字节时间戳
            # 头部: 模式/层/精度/根延迟/根离散/参考ID
            # 时间: 参考/起源/接收/发送时间
            response = struct.pack('!BBBBIIIQQQQ',
                                   mode_version, stratum, poll, precision,
                                   0, 0, 0,  # 根延迟、根离散、参考ID
                                   0,        # 参考时间 (假设为0)
                                   ntp_fields[8],  # 原始请求的起源时间
                                   ntp_fields[9],  # 原始请求的接收时间
                                   current_time,   # 发送时间
                                   current_time)   # 再次发送时间 (NTPv4)

            # 发送响应
            server_socket.sendto(response, client_address)
            print(f"已发送时间响应给 {client_address}")

        except Exception as e:
            print(f"服务器错误: {e}")

if __name__ == "__main__":
    import time
    # 默认 NTP 端口为 123，但在 Windows 上绑定 123 需要管理员权限
    # 为了测试方便，通常使用大于 1024 的端口
    port = 12345
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    ntp_server(port)