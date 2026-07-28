from collections import deque


def solution(n, infection, edges, k):
    # 1. 트리를 인접 리스트로 저장
    graph = [[] for _ in range(n + 1)]

    for x, y, pipe_type in edges:
        graph[x].append((y, pipe_type))
        graph[y].append((x, pipe_type))

    answer = 1

    # 2. 특정 타입의 파이프를 열었을 때 감염을 확산하는 함수
    def spread(infected, selected_type):
        next_infected = infected[:]
        queue = deque()

        # 현재 감염된 모든 노드가 감염 확산의 시작점
        for node in range(1, n + 1):
            if next_infected[node]:
                queue.append(node)

        while queue:
            current = queue.popleft()

            for next_node, pipe_type in graph[current]:
                # 현재 연 타입과 다른 파이프는 지나갈 수 없음
                if pipe_type != selected_type:
                    continue

                # 이미 감염된 노드는 다시 처리할 필요 없음
                if next_infected[next_node]:
                    continue

                next_infected[next_node] = True
                queue.append(next_node)

        return next_infected

    # 3. 파이프 타입을 여는 순서를 완전탐색
    def dfs(depth, infected, last_type):
        nonlocal answer

        infected_count = sum(infected)
        answer = max(answer, infected_count)

        # 모든 배양체가 감염됐다면 더 탐색할 필요 없음
        if infected_count == n:
            return

        # 최대 행동 횟수에 도달
        if depth == k:
            return

        # A, B, C 타입을 각각 선택
        for selected_type in range(1, 4):
            # 같은 타입을 연속해서 여는 것은 의미가 없음
            if selected_type == last_type:
                continue

            next_infected = spread(infected, selected_type)

            dfs(
                depth + 1,
                next_infected,
                selected_type
            )

    # 처음에는 infection 노드 하나만 감염
    initial_infected = [False] * (n + 1)
    initial_infected[infection] = True

    dfs(0, initial_infected, 0)

    return answer
