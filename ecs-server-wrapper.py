import os
import signal
import socket
import subprocess
import sys
import time

SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))
CACHE_FOLDER = os.path.join(SCRIPT_FOLDER, ".cache")
FIVE_SECONDS_DELAY = 5


def run(command):
    if not os.path.exists(CACHE_FOLDER):
        os.mkdir(CACHE_FOLDER)

    port = 9988
    python_file = 'ecs-server.py'
    pid_file = os.path.join(CACHE_FOLDER, "pid-" + str(port))

    if command == "start":
        print "Will run and detach from CLI and return to prompt..."
        run_python(python_file, port, pid_file, False)
        wait_until_port_is_open(port, 5, 5)

    if command == "status":
        wait_until_port_is_open(port, 1, 0)

    if command == "stop":
        kill_process(pid_file)
        wait_until_port_is_closed(port, 5, 5)

    if command == "console":
        print "Entered console mode (blocking, Ctrl-C to breakout)..."
        run_python(python_file, port, pid_file, True)


def run_python(python_path, port, pid_file, consoleMode):
    if consoleMode:
        proc = subprocess.call(["python", python_path, str(port)], cwd=SCRIPT_FOLDER)
    else:
        proc = subprocess.Popen(["python", python_path, str(port), "&", ], cwd=SCRIPT_FOLDER)

    f = open(pid_file, "w")
    f.write(str(proc.pid))
    f.close()
    print "Process running as pid: " + str(proc.pid)
    return proc.pid


def wait_until_port_is_open(port, count, delay):
    n = 0
    while True:
        print "Is application listening on port " + str(port) + "? "
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        if result == 0:
            print "Yes"
            return

        n = n + 1
        if n < count:
            print "No. Retrying in " + str(delay) + " seconds"
            time.sleep(delay)
        else:
            print "No."
            return


def wait_until_port_is_closed(port, count, delay):
    n = 0
    while True:
        print "Is application listening on port " + str(port) + "? "
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', int(port)))
        if result != 0:
            print "No"
            return

        n = n + 1
        if n < count:
            print "Yes. Retrying in " + str(delay) + " seconds"
            time.sleep(delay)
        else:
            print "Yes."
            return


def kill_process(pid_file):
    if not os.path.exists(pid_file):
        print "Already stopped."
        return

    f = open(pid_file, "r")
    try:
        pid_str = f.read()
        print "Kill process with pid: " + pid_str
        os.kill(int(pid_str), signal.SIGTERM)
    except Exception:
        f.close()
        os.remove(pid_file)


if __name__ == "__main__":
    run(sys.argv[1])
