import os
import signal
import socket
import subprocess
import sys
import time

CURRENT_DIR = os.getcwd()
SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))
CACHE_FOLDER = os.path.join(SCRIPT_FOLDER, ".cache")
FIVE_SECONDS_DELAY = 5


def run(argv):
    command = get_arg(argv, 1, "command")
    if not os.path.exists(CACHE_FOLDER):
        os.mkdir(CACHE_FOLDER)

    port = 9988
    python_file = 'ecs-server.py'
    pid_file = os.path.join(CACHE_FOLDER, "pid-" + str(port))

    if command == "start":
        print("Will run and detach from CLI and return to prompt...")
        json_task_env_file = get_arg(argv, 2, "JSON ENV task file")
        run_python(python_file, port, json_task_env_file, pid_file, False)
        wait_until_port_is_open(port, 5, 5)

    if command == "status":
        wait_until_port_is_open(port, 1, 0)

    if command == "stop":
        kill_process(pid_file)
        wait_until_port_is_closed(port, 5, 5)

    if command == "console":
        print("Entered console mode (blocking, Ctrl-C to breakout)...")
        json_task_env_file = get_arg(argv, 2, "JSON ENV task file")
        run_python(python_file, port, json_task_env_file, pid_file, True)


def get_arg(argv, index, arg_name):
    if index >= len(argv):
        raise Exception("Not enough parameters. Please provide "+arg_name)

    return argv[index]


def as_absolute(json_task_env_file):
    return os.path.join(os.getcwd(), json_task_env_file)


def run_python(python_path, port, json_task_env_file, pid_file, console_mode):
    if console_mode:
        proc = subprocess.call(["python3", python_path, str(port), as_absolute(json_task_env_file)], cwd=SCRIPT_FOLDER)
    else:
        proc = subprocess.Popen(["python3", python_path, str(port), as_absolute(json_task_env_file), "&", ], cwd=SCRIPT_FOLDER)

    f = open(pid_file, "w")
    f.write(str(proc.pid))
    f.close()
    print("Process running as pid: " + str(proc.pid))
    return proc.pid


def wait_until_port_is_open(port, count, delay):
    n = 0
    while True:
        print("Is application listening on port " + str(port) + "? ")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        if result == 0:
            print("Yes")
            return

        n = n + 1
        if n < count:
            print("No. Retrying in " + str(delay) + " seconds")
            time.sleep(delay)
        else:
            print("No.")
            return


def wait_until_port_is_closed(port, count, delay):
    n = 0
    while True:
        print("Is application listening on port " + str(port) + "? ")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', int(port)))
        if result != 0:
            print("No")
            return

        n = n + 1
        if n < count:
            print("Yes. Retrying in " + str(delay) + " seconds")
            time.sleep(delay)
        else:
            print("Yes.")
            return


def kill_process(pid_file):
    if not os.path.exists(pid_file):
        print("Already stopped.")
        return

    f = open(pid_file, "r")
    try:
        pid_str = f.read()
        print("Kill process with pid: " + pid_str)
        os.kill(int(pid_str), signal.SIGTERM)
    except Exception:
        f.close()
        os.remove(pid_file)


if __name__ == "__main__":
    run(sys.argv)
