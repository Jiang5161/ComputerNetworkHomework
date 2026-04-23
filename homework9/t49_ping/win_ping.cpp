// 编译 (使用 MSVC): cl win_ping.cpp Iphlpapi.lib /utf-8
// 运行: .\win_ping.exe <目标IP地址>

#include <iostream>
#include <windows.h>
#include <iphlpapi.h>
#include <icmpapi.h>

#pragma comment(lib, "iphlpapi.lib")

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <Target IP Address>" << std::endl;
        return 1;
    }

    const char* target_ip = argv[1];
    HANDLE hIcmp;
    IPAddr ip_addr;
    char send_data[32] = "Ping from C++";
    LPVOID reply_buffer;
    DWORD reply_size;
    DWORD status;

    // 1. Create ICMP handle
    hIcmp = IcmpCreateFile();
    if (hIcmp == INVALID_HANDLE_VALUE) {
        std::cerr << "Create ICMP handle failed, Error: " << GetLastError() << std::endl;
        return 1;
    }

    // 2. Convert IP address
    ip_addr = inet_addr(target_ip);
    if (ip_addr == INADDR_NONE) {
        std::cerr << "Invalid IP address: " << target_ip << std::endl;
        IcmpCloseHandle(hIcmp);
        return 1;
    }

    // 3. Prepare reply buffer
    reply_size = sizeof(ICMP_ECHO_REPLY) + 32;
    reply_buffer = (LPVOID)LocalAlloc(LPTR, reply_size);
    if (reply_buffer == NULL) {
        std::cerr << "Memory allocation failed" << std::endl;
        IcmpCloseHandle(hIcmp);
        return 1;
    }

    std::cout << "Pinging " << target_ip << " with " << 32 << " bytes of data:" << std::endl;

    // 4. Send Ping request
    for (int i = 0; i < 4; ++i) {
        status = IcmpSendEcho(hIcmp, ip_addr, send_data, 32, NULL, reply_buffer, reply_size, 1000);
        
        if (status == 0) {
            std::cout << "Request timed out." << std::endl;
        } else {
            ICMP_ECHO_REPLY* reply = (ICMP_ECHO_REPLY*)reply_buffer;
            if (reply->Status == IP_SUCCESS) {
                std::cout << "Reply from " << target_ip 
                          << ": bytes=" << reply->DataSize 
                          << " time=" << reply->RoundTripTime << "ms " 
                          << "TTL=" << (int)reply->Options.Ttl << std::endl;
            } else {
                std::cout << "Ping failed, Status: " << reply->Status << std::endl;
            }
        }
        Sleep(1000);
    }

    // 5. Cleanup
    LocalFree(reply_buffer);
    IcmpCloseHandle(hIcmp);
    return 0;
}