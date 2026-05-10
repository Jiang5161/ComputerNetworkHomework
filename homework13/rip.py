def rip_update(r1_table, r2_table, r2_name="R2"):
    """
    模拟 RIP 路由更新算法。

    参数:
    r1_table: 字典，R1 当前的路由表。格式: {'NetIP': [distance, next_hop], ...}
    r2_table: 字典，R2 发来的路由表（距离向量）。格式: {'NetIP': distance, ...}
    r2_name: 字符串，邻居路由器的名字（默认为 "R2"）。

    返回:
    更新后的 R1 路由表。
    """
    print(f"--- 开始处理来自 {r2_name} 的更新 ---")

    # 遍历 R2 发来的每一个路由条目
    for dest_net, r2_dist in r2_table.items():
        # R1 通过 R2 到达目的网络的新距离
        # RIP 中，邻居之间的跳数为 1，所以新距离 = R2的距离 + 1
        new_dist = r2_dist + 1

        if dest_net not in r1_table:
            # 情况 1: R1 路由表中没有该网络 -> 新增
            print(f"发现新网络 {dest_net}。添加路由: 距离={new_dist}, 下一跳={r2_name}")
            r1_table[dest_net] = [new_dist, r2_name]

        else:
            # 情况 2 & 3: R1 路由表中已有该网络
            current_dist, current_next_hop = r1_table[dest_net]

            if current_next_hop == r2_name:
                # 情况 2: 下一跳就是 R2 -> 无条件更新（无论距离变大还是变小）
                print(f"更新来自下一跳 {r2_name} 的网络 {dest_net}。距离更新为: {new_dist}")
                r1_table[dest_net] = [new_dist, r2_name]

            else:
                # 情况 3: 下一跳不是 R2 -> 只有当新路径更短时才更新
                if new_dist < current_dist:
                    print(f"发现更短路径到 {dest_net} (原:{current_dist} vs 新:{new_dist})。更新下一跳为 {r2_name}")
                    r1_table[dest_net] = [new_dist, r2_name]
                else:
                    # 距离更长或相等，保持原样
                    pass

    return r1_table


def print_routing_table(table):
    """格式化打印路由表"""
    print(f"{'目的网络':<15} {'距离':<10} {'下一跳':<10}")
    print("-" * 35)
    for net, (dist, hop) in sorted(table.items()):
        print(f"{net:<15} {dist:<10} {hop:<10}")
    print("-" * 35)


# --- 测试示例 ---

# 假设 R1 的初始路由表
# 格式: 网络: [距离, 下一跳]
r1_initial = {
    '192.168.1.0': [1, 'Direct'], # 直连
    '10.0.0.0':    [2, 'R3'],     # 通过 R3
    '172.16.0.0':  [4, 'R5']      # 通过 R5
}

# 假设 R2 发来的路由表
# 格式: 网络: 距离
r2_update = {
    '192.168.1.0': [10],   # 情况：R2 到该网络变远了（R1 应忽略，因为下一跳不是 R2）
    '10.0.0.0':    [1],    # 情况：R2 提供了更短的路径到 10.0.0.0 (1+1=2，这里相等不更新，若 R2 距离为 0 则更新)
    '172.16.0.0':  [2],    # 情况：R2 提供了更短路径 (2+1=3 < 4)，应更新
    '192.168.2.0': [1]     # 情况：新网络，应添加
}

print("R1 初始路由表:")
print_routing_table(r1_initial)

# 执行更新
updated_table = rip_update(r1_initial, r2_update, "R2")

print("\nR1 更新后的路由表:")
print_routing_table(updated_table)