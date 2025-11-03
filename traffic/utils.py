import math
import random
from collections import deque

# ------------------ Floyd–Warshall ------------------
def floyd_warshall(nodes, edges):
    n = len(nodes)
    dist = [[math.inf] * n for _ in range(n)]
    next_node = [[None] * n for _ in range(n)]

    for i in range(n):
        dist[i][i] = 0

    for u, v, w in edges:
        dist[u][v] = w
        next_node[u][v] = v

    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    next_node[i][j] = next_node[i][k]
    return dist, next_node


# ------------------ Ford–Fulkerson ------------------
def bfs(rGraph, s, t, parent):
    visited = [False] * len(rGraph)
    queue = deque([s])
    visited[s] = True
    while queue:
        u = queue.popleft()
        for v, cap in enumerate(rGraph[u]):
            if not visited[v] and cap > 0:
                queue.append(v)
                visited[v] = True
                parent[v] = u
    return visited[t]

def ford_fulkerson(graph, source, sink):
    n = len(graph)
    rGraph = [row[:] for row in graph]
    parent = [-1] * n
    max_flow = 0

    while bfs(rGraph, source, sink, parent):
        path_flow = float("inf")
        v = sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, rGraph[u][v])
            v = parent[v]
        v = sink
        while v != source:
            u = parent[v]
            rGraph[u][v] -= path_flow
            rGraph[v][u] += path_flow
            v = parent[v]
        max_flow += path_flow
    return max_flow


# ------------------ Simulate Live Traffic ------------------
def simulate_live_traffic(roads):
    for road in roads:
        # Simulate current flow between 50–150% of capacity
        road.current_flow = random.randint(
            int(0.5 * road.capacity), int(1.5 * road.capacity)
        )
        road.save()
