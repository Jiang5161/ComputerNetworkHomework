import heapq
from collections import defaultdict

def dijkstra(graph, start, end):
    """
    Dijkstra 算法核心实现
    :param graph: 邻接表表示的图 {节点: [(邻居, 权重), ...]}
    :param start: 起始节点
    :param end: 目标节点
    :return: (最短距离, 路径列表)
    """
    # 优先队列，存储 (当前距离, 当前节点)
    # 初始状态：起点的距离为 0
    pq = [(0, start)]
    
    # 记录从起点到各节点的最短距离，初始化为无穷大
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    
    # 记录路径的前驱节点，用于回溯路径
    # previous[node] = prev_node
    previous = {node: None for node in graph}
    
    while pq:
        # 弹出当前距离最小的节点
        current_dist, current_node = heapq.heappop(pq)
        
        # 如果弹出的距离大于记录的距离，说明已经处理过更优的路径，跳过
        if current_dist > distances[current_node]:
            continue
            
        # 如果到达目标节点，可以提前结束
        if current_node == end:
            break

        # 遍历当前节点的所有邻居
        for neighbor, weight in graph[current_node]:
            # 计算通过当前节点到达邻居的新距离
            new_dist = current_dist + weight
            
            # 如果找到更短的路径
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = current_node
                # 将新状态加入优先队列
                heapq.heappush(pq, (new_dist, neighbor))
    
    # 回溯路径
    path = []
    curr = end
    while curr is not None:
        path.append(curr)
        curr = previous[curr]
    path.reverse() # 反转路径，使其从起点到终点
    
    # 如果终点不可达（距离仍为无穷大）
    if distances[end] == float('inf'):
        return float('inf'), []
        
    return distances[end], path

def build_graph(edges):
    """
    根据输入的三元组列表构建邻接表
    """
    graph = defaultdict(list)
    # 确保所有节点都在图中（包括没有出边的叶子节点）
    all_nodes = set()
    
    for r1, r2, weight in edges:
        graph[r1].append((r2, weight))
        # 如果是无向图，需要添加反向边：graph[r2].append((r1, weight))
        # 这里默认按有向图处理，或者双向输入
        all_nodes.add(r1)
        all_nodes.add(r2)
        
    # 确保孤立节点也能被初始化（虽然对Dijkstra影响不大，但为了严谨）
    for node in all_nodes:
        if node not in graph:
            graph[node] = []
            
    return graph

# --- 主程序入口 ---

if __name__ == "__main__":
    print("请输入图的边信息，每行一个三元组，格式：节点A 节点B 权重")
    print("例如：r1 r2 5")
    print("输入 'END' 结束输入。")
    
    edges = []
    while True:
        line = input().strip()
        if line.upper() == 'END':
            break
        
        parts = line.split()
        if len(parts) == 3:
            r1, r2, w = parts[0], parts[1], int(parts[2])
            edges.append((r1, r2, w))
            # 如果是无向图，通常还需要添加 (r2, r1, w)，这里假设输入包含所有方向或为有向图
            # 若题目默认为无向图，请取消下面这行的注释：
            # edges.append((r2, r1, w))
        else:
            print("格式错误，请重新输入。")

    # 构建图
    graph = build_graph(edges)
    
    # 获取起点和终点
    start_node = input("请输入起点节点名称: ").strip()
    end_node = input("请输入终点节点名称: ").strip()
    
    # 运行算法
    distance, path = dijkstra(graph, start_node, end_node)
    
    # 输出结果
    if distance == float('inf'):
        print(f"从 {start_node} 到 {end_node} 没有可达路径。")
    else:
        print(f"最短距离: {distance}")
        print(f"最短路径: {' -> '.join(path)}")