import socket
import struct
import time

def main():
    # 创建原始套接字
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except PermissionError:
        print("需要管理员/root 权限")
        return

    # 设置目标服务器地址 
    server_ip = "127.0.0.1"  # 测试用本地回环

    # 构造 ICMP 时间请求
    icmp_type = 13  # 时间请求
    icmp_code = 0
    icmp_checksum = 0
    icmp_id = 1234
    icmp_seq = 1
    # 请求报文中时间字段通常为 0
    send_time = 0
    recv_time = 0
    trans_time = 0

    packet = struct.pack('!BBHHIII', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq, send_time, recv_time, trans_time)
    
    # 计算校验和
    def calculate_checksum(data):
        if len(data) % 2 == 1:
            data += b'\x00'
        checksum = 0
        for i in range(0, len(data), 2):
            w = (data[i] << 8) + data[i+1]
            checksum += w
        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += (checksum >> 16)
        return ~checksum & 0xffff

    checksum = calculate_checksum(packet)
    packet = struct.pack('!BBHIII', icmp_type, icmp_code, checksum, icmp_id, icmp_seq, send_time, recv_time, trans_time)

    # 发送请求
    sock.sendto(packet, (server_ip, 0))
    print(f"已发送 ICMP 时间请求到 {server_ip}")

    # 接收应答
    try:
        data, addr = sock.recvfrom(1024)
        if len(data) >= 20:  # ICMP 头部至少 8 字节 + 时间字段 12 字节
            # 解析时间字段 (第 21 字节开始)
            # 注意：网络字节序是大端
            recv_time_bytes = data[20:24]
            ntp_time = struct.unpack('!I', recv_time_bytes)[0]
            
            # 转换为 Unix 时间戳
            ntp_epoch_offset = 2208988800
            unix_time = ntp_time / 1000.0 - ntp_epoch_offset
            
            print(f"从服务器 {addr} 接收到时间: {time.ctime(unix_time)}")
    except socket.timeout:
        print("请求超时")
    except Exception as e:
        print(f"解析错误: {e}")

    sock.close()

if __name__ == "__main__":
    main()