import socket
import struct
import os

# 多播配置
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007
CHUNK_SIZE = 64 * 1024

def receive_file():
    # 创建UDP套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    # 允许端口复用
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 绑定端口
    sock.bind(('', MCAST_PORT))
    # 加入多播组
    mreq = struct.pack('4s4s', socket.inet_aton(MCAST_GRP), socket.inet_aton('0.0.0.0'))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # 接收文件名
    filename, _ = sock.recvfrom(1024)
    filename = filename.decode()
    print(f"接收文件: {filename}")

    # 接收文件内容并保存
    with open(filename, 'wb') as f:
        while True:
            chunk, _ = sock.recvfrom(CHUNK_SIZE)
            if not chunk:
                break
            f.write(chunk)
    print(f"文件 {filename} 接收并保存完成")

if __name__ == "__main__":
    receive_file()