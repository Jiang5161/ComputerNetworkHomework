import socket
import time
import struct

def main():
    # 创建原始套接字，使用 ICMP 协议
    # 注意：在某些系统上运行此代码需要管理员权限
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except PermissionError:
        print("需要管理员/root 权限来创建原始套接字")
        return

    # 绑定到所有接口，端口不适用 ICMP，但需要绑定地址
    sock.bind(('', 0))
    
    print("ICMP 时间服务器正在运行，等待请求...")

    while True:
        try:
            # 接收数据
            data, addr = sock.recvfrom(1024)
            print(f"收到来自 {addr} 的请求")

            # 解析 ICMP 请求 (类型 13 是时间请求，14 是时间应答)
            # 这里简化处理，直接构造应答
            icmp_type = 14  # 时间应答
            icmp_code = 0
            icmp_checksum = 0
            icmp_id = 1234  # 简单 ID
            icmp_seq = 1    # 序列号

            # 获取当前时间 (自 1900-01-01 00:00:00 UTC 的毫秒数)
            # time.time() 返回秒数，转换为毫秒并加上偏移量
            ntp_epoch_offset = 2208988800  # 1900 到 1970 的秒数
            current_time = int((time.time() + ntp_epoch_offset) * 1000)

            # 构造 ICMP 时间报文
            # 类型(1) + 代码(1) + 校验和(2) + ID(2) + 序列号(2) + 发送时间(4) + 接收时间(4) + 传输时间(4)
            # 对于应答，发送、接收、传输时间都设为当前时间
            packet = struct.pack('!BBHHIII', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq, current_time, current_time, current_time)
            
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
            packet = struct.pack('!BBHIII', icmp_type, icmp_code, checksum, icmp_id, icmp_seq, current_time, current_time, current_time)

            # 发送应答
            sock.sendto(packet, addr)
            print(f"已发送时间应答给 {addr}")

        except Exception as e:
            print(f"服务器错误: {e}")
            break

    sock.close()

if __name__ == "__main__":
    main()