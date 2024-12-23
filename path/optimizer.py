import itertools

from heapq import heappush, heappop
    
class Graph:
    def __init__(self, adjacency_list):
        self.adjacency_list = adjacency_list

class Vertex:
    def __init__(self, value, longitude):
        self.value = value
        self.longitude = longitude

class Edge:
    def __init__(self, cost, vertex):
        self.cost = cost
        self.vertex = vertex
    
def dijkstra(graph, start, end):
    previous = {v: None for v in graph.adjacency_list.keys()}
    visited = {v: False for v in graph.adjacency_list.keys()}
    costs = {v: float('inf') for v in graph.adjacency_list.keys()}
    costs[start] = 0
    queue = PriorityQueue()
    queue.add_task(0, start)
    path = []
    last_visited = None 
    
    while queue:
        removed_cost, removed = queue.pop_task()
        visited[removed] = True
        last_visited = removed  # update the last visited vertex

        if removed is end:
            while previous[removed]:
                path.append(removed.value)
                removed = previous[removed]
            path.append(start.value)
            return path[::-1], costs[end]

        for edge in graph.adjacency_list[removed]:
            if visited[edge.vertex]:
                continue

            new_cost = removed_cost + edge.cost
            if new_cost < costs[edge.vertex]:
                costs[edge.vertex] = new_cost
                previous[edge.vertex] = removed
                queue.add_task(new_cost, edge.vertex)
    # if no path is found.
    print(f'No complete path found!')
    return [last_visited.value], costs[last_visited]

class PriorityQueue:

    def __init__(self):
        self.pq = []  # list of entries arranged in a heap
        self.entry_finder = {}  # mapping of tasks to entries
        self.counter = itertools.count()  # unique sequence count

    def __len__(self):
        return len(self.pq)

    def add_task(self, priority, task):
        # add a new task or update the priority of an existing task
        if task in self.entry_finder:
            self.update_priority(priority, task)
            return self
        count = next(self.counter)
        entry = [priority, count, task]
        self.entry_finder[task] = entry
        heappush(self.pq, entry)

    def update_priority(self, priority, task):
        # update the priority of a task in place
        entry = self.entry_finder[task]
        count = next(self.counter)
        entry[0], entry[1] = priority, count

    def pop_task(self):
        # remove and return the lowest priority task. Raise KeyError if empty.
        while self.pq:
            priority, count, task = heappop(self.pq)
            del self.entry_finder[task]
            return priority, task
        raise KeyError('pop from an empty priority queue')