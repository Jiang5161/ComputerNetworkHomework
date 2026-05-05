import threading
import time
import random
import queue

# 模拟网络环境，有一定丢包率
LOSS_RATE = 0.2  # 20% 丢包率

class StopAndWait:
    def __init__(self):
        self.send_queue = queue.Queue()
        self.recv_queue = queue.Queue()
        self.running = True
        self.seq_num = 0  # 当前序列号

    def sender(self):
        packet_id = 0
        while self.running:
            # 模拟发送数据包
            if random.random() > LOSS_RATE:
                print(f"[发送方] 发送包 {packet_id} (序列号: {self.seq_num})")
                # 将包放入模拟的接收队列，模拟网络传输
                self.recv_queue.put((packet_id, self.seq_num))
                
                # 启动超时计时器等待 ACK
                start_time = time.time()
                ack_received = False
                
                while time.time() - start_time < 1:  # 1秒超时
                    # 检查是否有 ACK
                    if not self.send_queue.empty():
                        ack = self.send_queue.get()
                        if ack == self.seq_num:
                            print(f"[发送方] 收到 ACK {ack}，发送下一个包")
                            self.seq_num = 1 - self.seq_num  # 翻转序列号
                            packet_id += 1
                            ack_received = True
                            break
                        else:
                            print(f"[发送方] 收到错误的 ACK {ack}，丢弃")
                    time.sleep(0.1)
                
                if not ack_received:
                    print(f"[发送方] 超时，重传包 {packet_id}")
                    # 不增加 packet_id，重传当前包
                    continue
            else:
                print(f"[发送方] 发送包 {packet_id} 时发生丢包")
                # 模拟丢包，不放入 recv_queue

            # 短暂休眠，模拟发送间隔
            time.sleep(0.5)
            
            # 简单控制，发送几个包后停止
            if packet_id > 5:
                break

    def receiver(self):
        while self.running:
            try:
                # 模拟接收数据包
                packet_id, seq = self.recv_queue.get(timeout=0.5)
                
                # 模拟网络处理延迟
                time.sleep(0.2)
                
                # 模拟 ACK 发送（可能丢包）
                if random.random() > LOSS_RATE:
                    print(f"[接收方] 正确接收包 {packet_id} (序列号: {seq})，发送 ACK {seq}")
                    self.send_queue.put(seq)
                else:
                    print(f"[接收方] 接收包 {packet_id} 后，ACK {seq} 发送时丢包")
                
            except queue.Empty:
                continue

def main():
    protocol = StopAndWait()
    
    # 创建发送和接收线程
    sender_thread = threading.Thread(target=protocol.sender)
    receiver_thread = threading.Thread(target=protocol.receiver)
    
    # 启动线程
    sender_thread.start()
    receiver_thread.start()
    
    # 等待线程结束
    sender_thread.join()
    receiver_thread.join()
    
    print("停等协议模拟结束")

if __name__ == "__main__":
    main()