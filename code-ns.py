import time

print(time.monotonic_ns())

min_diff = -1
max_loops = 0

while True:
    loops = 0
    a = time.monotonic_ns()
    b = a
    while b == a:
        b = time.monotonic_ns()
        loops += 1
    diff = b - a
    if min_diff == -1 or diff < min_diff:
        print(diff)
        min_diff = diff
    if loops > max_loops:
        print(loops)
        max_loops = loops
