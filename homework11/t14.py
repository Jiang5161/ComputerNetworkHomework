import threading
import time
import random
import queue

# 模拟参数
WINDOW_SIZE = 5
TOTAL_PACKETS = 15
LOSS_RATE = 0.1  # 10% 丢包率
TIMEOUT = 2      # 2秒超时

class SlidingWindow:
    def __init__(self):
        self.packets = list(range(TOTAL_PACKETS))
        self.base = 0           # 窗口基序号
        self.next_seq = 0      # 下一个要发送的序号
        self.acked = [False] * TOTAL_PACKETS  # 确认状态
        self.sent_time = [0] * TOTAL_PACKETS  # 发送时间记录
        
        # 模拟队列
        self.network_queue = queue.Queue()
        self.ack_queue = queue.Queue()
        
        self.running = True
        self.lock = threading.Lock()

    def sender(self):
        while self.running:
            with self.lock:
                # 发送窗口内未发送的数据
                while self.next_seq < self.base + WINDOW_SIZE and self.next_seq < TOTAL_PACKETS:
                    if not self.acked[self.next_seq]:
                        # 模拟丢包
                        if random.random() > LOSS_RATE:
                            current_time = time.time()
                            self.sent_time[self.next_seq] = current_time
                            print(f"[发送方] 发送包 {self.next_seq} 时间: {current_time:.2f}")
                            self.network_queue.put(self.next_seq)
                        else:
                            print(f"[发送方] 包 {self.next_seq} 发送丢包")
                        self.next_seq += 1
                    else:
                        break
                
                # 检查超时重传
                for seq in range(self.base, min(self.base + WINDOW_SIZE, TOTAL_PACKETS)):
                    if not self.acked[seq] and time.time() - self.sent_time[seq] > TIMEOUT:
                        print(f"[发送方] 包 {seq} 超时，重传")
                        self.sent_time[seq] = time.time()
                        self.network_queue.put(seq)
                
                # 移动窗口
                while self.base < TOTAL_PACKETS and self.acked[self.base]:
                    self.base += 1
                
                # 检查是否完成
                if self.base >= TOTAL_PACKETS:
                    self.running = False
                    print("[发送方] 所有数据发送完成")
            
            time.sleep(0.5)  # 模拟发送间隔

    def receiver(self):
        received_packets = []
        while self.running or not self.network_queue.empty():
            try:
                # 接收数据包
                seq = self.network_queue.get(timeout=0.5)
                
                # 模拟接收处理
                time.sleep(0.3)
                
                # 模拟 ACK 丢包
                if random.random() > LOSS_RATE:
                    print(f"[接收方] 接收包 {seq}，发送 ACK {seq}")
                    self.ack_queue.put(seq)
                    received_packets.append(seq)
                else:
                    print(f"[接收方] 接收包 {seq}，ACK {seq} 发送丢包")
                    
            except queue.Empty:
                continue

    def monitor(self):
        """监控窗口状态"""
        while self.running:
            with self.lock:
                print("\n--- 窗口状态监控 ---")
                print(f"已发送并收到确认: {list(range(0, self.base))}")
                print(f"已发送但未收到确认: {list(range(self.base, self.next_seq))}")
                print(f"允许发送但尚未发送: {list(range(self.next_seq, min(self.base + WINDOW_SIZE, TOTAL_PACKETS)))}")
                print(f"不允许发送: {list(range(min(self.base + WINDOW_SIZE, TOTAL_PACKETS), TOTAL_PACKETS))}")
                print(f"接收窗口允许接收: {list(range(self.base, min(self.base + WINDOW_SIZE, TOTAL_PACKETS)))}")
                print(f"拥塞窗口大小: {WINDOW_SIZE}, 可用窗口: {max(0, self.base + WINDOW_SIZE - self.next_seq)}")
            time.sleep(1)
        print("监控结束")

def main():
    protocol = SlidingWindow()
    
    # 创建线程
    sender_thread = threading.Thread(target=protocol.sender)
    receiver_thread = threading.Thread(target=protocol.receiver)
    monitor_thread = threading.Thread(target=protocol.monitor)
    
    # 启动线程
    sender_thread.start()
    receiver_thread.start()
    monitor_thread.start()
    
    # 等待完成
    sender_thread.join()
    receiver_thread.join()
    protocol.running = False
    monitor_thread.join()

if __name__ == "__main__":
    main()