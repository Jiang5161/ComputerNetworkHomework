// 编译: cl raw_dhcp_server.cpp ws2_32.lib
// 运行: 必须以管理员身份运行

#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <iostream>
#include <vector>

#pragma comment(lib, "ws2_32.lib")

#define DHCP_SERVER_PORT 67
#define DHCP_CLIENT_PORT 68
#define MAX_PACKET_SIZE 576

// --- 结构体定义 ---
struct dhcp_packet {
    uint8_t  op, htype, hlen, hops;
    uint32_t xid;
    uint16_t secs, flags;
    uint32_t ciaddr, yiaddr, siaddr, giaddr;
    uint8_t  chaddr[16];
    uint8_t  sname[64], file[128];
    uint8_t  options[312];
};

// --- 校验和计算函数 ---
unsigned short checksum(unsigned short* buf, int size) {
    unsigned long sum = 0;
    while (size > 1) { sum += *buf++; size -= 2; }
    if (size) sum += *(unsigned char*)buf;
    while (sum >> 16) sum = (sum & 0xFFFF) + (sum >> 16);
    return (unsigned short)(~sum);
}

int main() {
    WSADATA wsaData;
    SOCKET sock;
    sockaddr_in serverAddr, clientAddr;
    dhcp_packet packet;
    int addrLen = sizeof(clientAddr);

    // 1. 初始化 Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup 失败" << std::endl;
        return 1;
    }

    // 2. 创建 UDP 套接字
    sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock == INVALID_SOCKET) {
        std::cerr << "Socket 创建失败: " << WSAGetLastError() << std::endl;
        return 1;
    }

    // 3. 允许广播
    BOOL bBroadcast = TRUE;
    setsockopt(sock, SOL_SOCKET, SO_BROADCAST, (char*)&bBroadcast, sizeof(bBroadcast));

    // 4. 绑定端口
    memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY; // 监听所有网卡
    serverAddr.sin_port = htons(DHCP_SERVER_PORT);

    if (bind(sock, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        std::cerr << "Bind 失败 (端口 67 可能被占用或无权限): " << WSAGetLastError() << std::endl;
        std::cerr << "请尝试以管理员身份运行。" << std::endl;
        closesocket(sock);
        WSACleanup();
        return 1;
    }

    std::cout << "DHCP 服务器 (Raw Socket) 已启动..." << std::endl;

    while (true) {
        memset(&packet, 0, sizeof(packet));
        
        // 5. 接收数据
        int recvSize = recvfrom(sock, (char*)&packet, sizeof(packet), 0, (sockaddr*)&clientAddr, &addrLen);
        if (recvSize == SOCKET_ERROR) continue;

        // 6. 简单解析 (检查是否为 Discover, 类型 53 = 1)
        // 注意：实际解析需要遍历 options 字段，这里简化处理
        // 假设收到的包是 Discover，我们直接回复 Offer
        
        std::cout << "收到请求，准备分配 IP..." << std::endl;

        // 7. 构造 Offer 包
        dhcp_packet offer;
        memset(&offer, 0, sizeof(offer));
        
        offer.op = 2; // Boot Reply
        offer.htype = 1;
        offer.hlen = 6;
        offer.xid = packet.xid;
        
        // 设置要分配的固定 IP (例如 192.168.1.200)
        offer.yiaddr = inet_addr("192.168.1.200"); 
        offer.siaddr = inet_addr("192.168.1.100"); // 服务器 IP
        
        memcpy(offer.chaddr, packet.chaddr, 16);

        // 设置 Options (简化版)
        uint8_t* opt = offer.options;
        *opt++ = 53; *opt++ = 1; *opt++ = 2; // Message Type: Offer
        *opt++ = 54; *opt++ = 4; // Server ID
        uint32_t srvIp = inet_addr("192.168.1.100");
        memcpy(opt, &srvIp, 4); opt += 4;
        *opt++ = 1; *opt++ = 4; // Subnet Mask
        uint32_t mask = inet_addr("255.255.255.0");
        memcpy(opt, &mask, 4); opt += 4;
        *opt++ = 255; // End

        // 8. 发送广播
        sockaddr_in broadcastAddr;
        memset(&broadcastAddr, 0, sizeof(broadcastAddr));
        broadcastAddr.sin_family = AF_INET;
        broadcastAddr.sin_addr.s_addr = INADDR_BROADCAST; // 255.255.255.255
        broadcastAddr.sin_port = htons(DHCP_CLIENT_PORT);

        sendto(sock, (char*)&offer, sizeof(offer), 0, (sockaddr*)&broadcastAddr, sizeof(broadcastAddr));
        std::cout << "已发送 Offer 广播" << std::endl;
    }

    closesocket(sock);
    WSACleanup();
    return 0;
}