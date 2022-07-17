import time
import multiprocessing


def cpu_bound(number):
    print()
    print(number)
    start_time = time.time()

    s=sum(i * i for i in range(number))

    duration = time.time() - start_time
    print(f"Duration {duration:.2f} seconds")

    return s

def find_sums(numbers):
    with multiprocessing.Pool() as pool:
        pool.map(cpu_bound, numbers)


if __name__ == "__main__":
    numbers = [5_000_000 + x for x in range(20)]
    print(numbers)

    start_time = time.time()
    find_sums(numbers)
    duration = time.time() - start_time
    print(f"Duration {duration:.2f} seconds")