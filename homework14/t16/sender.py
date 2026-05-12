import socket
import struct
import os

# 多播配置
MCAST_GRP = '224.1.1.1'  # 多播组地址
MCAST_PORT = 5007         # 多播端口
TTL = 2                   # 多播TTL（局域网内有效）
CHUNK_SIZE = 64 * 1024    # 每次发送64KB

def send_file(filepath):
    # 创建UDP套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    # 设置多播TTL
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', TTL))

    # 发送文件名（用于接收方保存）
    filename = os.path.basename(filepath)
    sock.sendto(filename.encode(), (MCAST_GRP, MCAST_PORT))

    # 发送文件内容
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            sock.sendto(chunk, (MCAST_GRP, MCAST_PORT))
    print(f"文件 {filename} 多播发送完成")

if __name__ == "__main__":
    send_file("large_file.bin")  