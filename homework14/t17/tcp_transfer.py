import socket
import os
import time
import threading

# 配置
HOST = '127.0.0.1'  # 本地回环地址，如果是局域网传输，发送方设为本机IP，接收方设为目标IP
PORT = 5008
CHUNK_SIZE = 1024 * 1024  # 1MB 缓冲区

def tcp_send(filepath, host=HOST, port=PORT):
    """
    TCP 发送端逻辑
    """
    if not os.path.exists(filepath):
        print(f"错误：文件 {filepath} 不存在！")
        return

    # 1. 创建套接字
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 2. 连接服务器
        client_socket.connect((host, port))
        print(f"已连接到 {host}:{port}")

        # 3. 准备文件信息
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)

        # 4. 发送头部信息 (文件名:大小)
        header = f"{filename}:{file_size}"
        client_socket.send(header.encode())

        # 5. 发送文件内容
        print(f"开始发送 {filename} ({file_size} 字节)...")
        start_time = time.time()

        with open(filepath, 'rb') as f:
            sent_bytes = 0
            while sent_bytes < file_size:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                client_socket.sendall(chunk)  # 使用 sendall 确保数据完整发送
                sent_bytes += len(chunk)

        end_time = time.time()
        print(f"发送完成！耗时: {end_time - start_time:.2f}秒")

    except Exception as e:
        print(f"发送出错: {e}")
    finally:
        client_socket.close()

def tcp_receive(host=HOST, port=PORT):
    """
    TCP 接收端逻辑 (修复了你截图中的缩进和逻辑)
    """
    # 1. 创建套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 允许端口复用，防止重启时报错 Address already in use
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # 2. 绑定并监听
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"等待连接在 {host}:{port}...")

        # 3. 接受连接
        conn, addr = server_socket.accept()
        print(f"连接来自: {addr}")

        with conn:
            # 4. 接收头部信息
            header_data = conn.recv(1024).decode()
            if not header_data:
                return

            filename, file_size_str = header_data.split(':')
            file_size = int(file_size_str)

            print(f"准备接收: {filename}, 大小: {file_size} 字节")

            # 5. 接收文件内容
            start_time = time.time()
            received = 0

            save_name = "received_" + filename

            with open(save_name, 'wb') as f:
                while received < file_size:
                    # 如果剩余数据小于CHUNK_SIZE，只接收剩余部分
                    to_receive = min(CHUNK_SIZE, file_size - received)
                    chunk = conn.recv(to_receive)

                    if not chunk:
                        break

                    f.write(chunk)
                    received += len(chunk)

            end_time = time.time()
            print(f"TCP接收完成！文件名: {save_name}")
            print(f"耗时: {end_time - start_time:.2f}秒")

    except Exception as e:
        print(f"接收出错: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    # 简单的测试逻辑：
    # 创建一个线程运行接收端，主线程运行发送端（仅用于本机测试）
    # 实际使用时，请分别在两台机器上运行 receive 和 send 函数

    test_file = "large_file.bin"

    # 创建一个测试大文件
    if not os.path.exists(test_file):
        print(f"正在生成测试文件 {test_file} (200MB)...")
        with open(test_file, 'wb') as f:
            f.write(os.urandom(200 * 1024 * 1024)) # 生成200MB随机数据

    # 启动接收端（模拟服务器）
    receiver_thread = threading.Thread(target=tcp_receive)
    receiver_thread.start()

    # 等待一会让服务器启动
    time.sleep(1)

    # 启动发送端
    tcp_send(test_file)

    # 等待接收线程结束
    receiver_thread.join()