import argparse  # Модуль для работы с аргументами командной строки
import multiprocessing  # Модуль для работы с параллельными процессами
import os  # Модуль для работы с операционной системой (например, очистка экрана)
import time  # Модуль для работы с временем (замер и форматирование времени)
from tabulate import tabulate  # Модуль для красивого вывода таблиц
from colorama import Fore, Style, init  # Модуль для раскраски текста в консоли

# Инициализация colorama для корректной работы в Windows
init()

# Функция для форматирования времени в удобный для чтения формат (часы:минуты:секунды)
def format_time(seconds):
    return time.strftime("%H:%M:%S", time.localtime(seconds))

# Функция, которую будут выполнять рабочие процессы
# task_queue - очередь задач, result_queue - очередь для результатов
# status - список статусов задач, start_times и end_times - время начала и завершения задач
# lock - блокировка для синхронизации доступа к общим ресурсам между процессами
def worker(task_queue, result_queue, status, start_times, end_times, lock):
    while True:
        try:
            # Извлекаем задачу из очереди
            idx, job, duration = task_queue.get_nowait()
        except multiprocessing.queues.Empty:
            # Если задач больше нет, выходим из цикла
            break

        # Захватываем блокировку, чтобы избежать конфликтов между процессами
        with lock:
            # Обновляем статус задачи на "Выполняется" и записываем время старта
            status[idx] = f"{Fore.YELLOW}Выполняется{Style.RESET_ALL}"
            start_times[idx] = format_time(time.time())

        # Эмулируем выполнение задачи с помощью задержки
        time.sleep(duration)

        # Обновляем статус задачи на "Выполнено" и записываем время завершения
        with lock:
            status[idx] = f"{Fore.GREEN}Выполнено{Style.RESET_ALL}"
            end_times[idx] = format_time(time.time())

# Основная функция, управляющая родительским процессом
# tasks - список задач, num_processes - количество параллельных процессов
def parent_process(tasks, num_processes):
    # Создаём менеджер для синхронизации данных между процессами
    manager = multiprocessing.Manager()

    # Очереди задач и результатов
    task_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()

    # Общие списки для хранения статусов задач и времени начала/завершения
    status = manager.list([f"{Fore.RED}Не выполняется{Style.RESET_ALL}"] * len(tasks))
    start_times = manager.list(["--:--:--"] * len(tasks))
    end_times = manager.list(["--:--:--"] * len(tasks))

    # Блокировка для синхронизации доступа к общим данным
    lock = manager.Lock()

    # Заполняем очередь задачами
    for idx, task in enumerate(tasks):
        task_queue.put((idx, task[0], task[1]))

    # Создаём процессы, которые будут выполнять задачи
    processes = []
    for _ in range(num_processes):
        p = multiprocessing.Process(target=worker, args=(task_queue, result_queue, status, start_times, end_times, lock))
        p.start()
        processes.append(p)

    # Пока не все задачи завершены, обновляем экран каждую секунду
    while True:
        # Если все задачи выполнены, прерываем цикл
        if task_queue.empty() and all(s == f"{Fore.GREEN}Выполнено{Style.RESET_ALL}" for s in status):
            break

        # Очищаем экран
        os.system('cls' if os.name == 'nt' else 'clear')

        # Создаём таблицу с текущим состоянием всех задач
        table = [[tasks[i][0], status[i], start_times[i], end_times[i]] for i in range(len(tasks))]
        print(tabulate(table, headers=["Задача", "Статус", "Начало", "Конец"]))

        # Ждём 1 секунду перед следующим обновлением
        time.sleep(1)

    # Ожидаем завершения всех процессов
    for p in processes:
        p.join()

    # Финальный вывод таблицы с результатами
    os.system('cls' if os.name == 'nt' else 'clear')
    table = [[tasks[i][0], status[i], start_times[i], end_times[i]] for i in range(len(tasks))]
    print(tabulate(table, headers=["Задача", "Статус", "Начало", "Конец"]))

# Функция для чтения задач из файла
# Каждая строка в файле должна быть в формате: "имя_задачи: время_выполнения"
def read_tasks(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        # Преобразуем каждую строку в кортеж (имя задачи, время выполнения)
        return [(line.split(': ')[0], int(line.split(': ')[1])) for line in f]

# Главная функция программы
def main():
    # Создаём парсер аргументов командной строки
    parser = argparse.ArgumentParser(description="Параллельное выполнение задач.")
    
    # Добавляем аргумент для количества процессов (-p)
    parser.add_argument('-p', type=int, required=True, help="Количество параллельных процессов.")
    
    # Добавляем аргумент для имени файла с задачами (-f)
    parser.add_argument('-f', type=str, required=True, help="Файл с задачами.")

    # Парсим аргументы
    args = parser.parse_args()

    # Читаем задачи из файла
    tasks = read_tasks(args.f)

    # Запускаем родительский процесс с задачами и указанным количеством процессов
    parent_process(tasks, args.p)

# Запускаем программу
if __name__ == "__main__":
    main()
