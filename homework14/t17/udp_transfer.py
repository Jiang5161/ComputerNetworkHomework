import socket
import os
import struct
import sys
import time

# 配置参数
HEADER_SIZE = 8  # 头部大小：4字节命令 + 4字节数据长度
CHUNK_SIZE = 64 * 1024  # 每次传输 64KB
TIMEOUT = 5  # 超时时间（秒）

def send_file(filename, host, port):
    """UDP 发送端 (带简单的停等协议以保证可靠性)"""
    if not os.path.exists(filename):
        print(f"错误: 文件 {filename} 不存在")
        return

    # 1. 创建 UDP 套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)  # 设置超时，用于重传

    file_size = os.path.getsize(filename)
    print(f"准备发送: {filename} ({file_size} 字节) 到 {host}:{port}...")

    try:
        # 2. 发送文件元数据 (文件名, 文件大小)
        # 格式: 文件名长度(4字节) + 文件名 + 文件大小(8字节)
        meta_data = struct.pack('!I', len(filename)) + filename.encode() + struct.pack('!Q', file_size)
        sock.sendto(meta_data, (host, port))
        print("已发送文件元数据，等待接收方确认...")

        # 等待接收方的 "READY" 信号
        ack, _ = sock.recvfrom(1024)
        if ack != b'READY':
            print("接收方未准备好，退出。")
            return
        print("接收方已准备好。开始传输数据...")

        # 3. 发送文件数据
        seq_num = 0  # 简单的序列号 (0 或 1)
        start_time = time.time()

        with open(filename, 'rb') as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break  # 文件读取完毕

                # 构造数据包: 序列号(1字节) + 数据
                packet = struct.pack('!B', seq_num) + chunk

                while True:
                    # 发送数据包
                    sock.sendto(packet, (host, port))

                    try:
                        # 等待 ACK
                        ack, _ = sock.recvfrom(1024)
                        # 解包 ACK 序列号
                        ack_seq = struct.unpack('!B', ack)[0]
                        if ack_seq == seq_num:
                            # 收到正确的确认，发送下一块
                            seq_num = 1 - seq_num  # 翻转序列号 0->1, 1->0
                            break
                    except socket.timeout:
                        # 超时，重传当前数据包
                        print(f"\n超时，重传数据包 (Seq={seq_num})...", end='\r')
                        continue

        # 4. 发送结束标志 (EOF)
        # 发送一个空的包或者特定标志告诉接收方结束
        eof_packet = struct.pack('!B', 255) # 使用 255 作为结束标志
        sock.sendto(eof_packet, (host, port))

        end_time = time.time()
        print(f"\n传输完成! 耗时: {end_time - start_time:.2f}秒")
        print(f"平均速度: {(file_size / 1024 / 1024) / (end_time - start_time):.2f} MB/s")

    finally:
        sock.close()

def receive_file(save_dir=".", host='0.0.0.0', port=5008):
    """UDP 接收端"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"UDP 接收端启动，监听 {host}:{port} ...")

    while True:
        # 1. 接收元数据
        data, addr = sock.recvfrom(65535)
        print(f"收到来自 {addr} 的连接请求...")

        # 解析元数据
        filename_len = struct.unpack('!I', data[:4])[0]
        filename = data[4:4+filename_len].decode()
        file_size = struct.unpack('!Q', data[4+filename_len:])[0]

        save_path = os.path.join(save_dir, filename)
        print(f"即将接收文件: {filename} (大小: {file_size} 字节)")
        print(f"保存路径: {save_path}")

        # 发送 "READY" 信号
        sock.sendto(b'READY', addr)

        # 2. 接收文件数据
        received_size = 0
        expected_seq = 0
        start_time = time.time()

        with open(save_path, 'wb') as f:
            while received_size < file_size:
                packet, _ = sock.recvfrom(CHUNK_SIZE + 10) # 数据 + 头部

                # 解析序列号
                seq_num = struct.unpack('!B', packet[:1])[0]

                # 检查是否为结束标志
                if seq_num == 255:
                    break

                # 如果是期望的序列号，写入文件并发送 ACK
                if seq_num == expected_seq:
                    f.write(packet[1:])
                    received_size += len(packet[1:])

                    # 发送 ACK
                    sock.sendto(struct.pack('!B', seq_num), addr)
                    expected_seq = 1 - expected_seq # 翻转期望的序列号

                    # 打印进度
                    percent = (received_size / file_size) * 100
                    print(f"进度: {percent:.2f}% ({received_size}/{file_size} 字节)", end='\r')
                else:
                    # 重复包或乱序包，重新发送上一个 ACK
                    sock.sendto(struct.pack('!B', 1 - expected_seq), addr)

        end_time = time.time()
        print(f"\n\n文件接收完毕: {save_path}")
        print(f"总耗时: {end_time - start_time:.2f}秒")

        # 询问是否继续监听
        print("-" * 30)

if __name__ == '__main__':
    # 使用方法:
    # 接收端: python udp_transfer.py recv
    # 发送端: python udp_transfer.py send <filename> <ip>

    if len(sys.argv) < 2:
        print("用法:")
        print("  接收模式: python udp_transfer.py recv [端口]")
        print("  发送模式: python udp_transfer.py send <文件路径> <目标IP> [端口]")
        sys.exit(1)

    mode = sys.argv[1]
    PORT = 5008

    if mode == 'recv':
        if len(sys.argv) > 2:
            PORT = int(sys.argv[2])
        receive_file(port=PORT)

    elif mode == 'send':
        if len(sys.argv) < 4:
            print("发送模式需要指定文件路径和目标IP")
            sys.exit(1)
        file_path = sys.argv[2]
        target_ip = sys.argv[3]
        if len(sys.argv) > 4:
            PORT = int(sys.argv[4])
        send_file(file_path, target_ip, PORT)
    else:
        print("未知模式，请使用 'send' 或 'recv'")