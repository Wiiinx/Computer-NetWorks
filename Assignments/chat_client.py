import sys
import select
from socket import *
import builtins

if len(sys.argv) != 3:
    print("Usage: python3 " + sys.argv[0] + "server_address server_port")
    sys.exit(1)


# Redefine print for autograder -- do not modify
def print(*args, **kwargs):
    builtins.print(*args, **kwargs, flush=True)


server_address = sys.argv[1]
relay_port = int(sys.argv[2])


client_socket = socket(AF_INET, SOCK_STREAM)

client_socket.connect((server_address, relay_port))
print(f"Connected to {server_address} on port {relay_port}\n")


stdin = sys.stdin.fileno()
all_fds = [stdin, client_socket.fileno()]  # Add your sockets fileno() here


while True:
    ready_fds, _, _ = select.select(all_fds, [], [], 5)

    for source in ready_fds:
        if source == stdin:
            message = sys.stdin.readline()
            if message.strip():
                # print("You typed:", message.strip())
                print("Sent:", message.strip())
                client_socket.sendall(message.encode())

        elif source == client_socket.fileno():
            data = client_socket.recv(1024)
            if data:
                print("Received:", data.decode())
            else:
                print("Disconnected from server")
                client_socket.close()
                sys.exit()

client_socket.close()
