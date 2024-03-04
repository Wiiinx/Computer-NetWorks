import sys
import select
from socket import *
import builtins

def print(*args, **kwargs):
    builtins.print(*args, **kwargs, flush=True)

bad_words = ["virus", "worm", "malware"]
good_words = ["groot", "hulk", "ironman"]

def replace_bad_words(s):
    for j in range(3):
        s = s.replace(bad_words[j], good_words[j])
    return s

if len(sys.argv) != 2:
    print("Usage: python3 " + sys.argv[0] + " port")
    sys.exit(1)
port = int(sys.argv[1])


# Create a TCP socket to listen on port for new connections
listener_socket = socket(AF_INET, SOCK_STREAM)
listener_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
listener_socket.bind(('', port))
listener_socket.listen()
print(f"Listening on port: {port} \n")
sockets_list = [listener_socket]
client_A = None
client_B = None

active = True

while active:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:
        if notified_socket == listener_socket:
            client_socket, client_address = listener_socket.accept()
            if not client_A:
                client_A = client_socket
                sockets_list.append(client_A)
                print(f"A: {client_address}")
            elif not client_B:
                client_B = client_socket
                sockets_list.append(client_B)
                print(f"B: {client_address}")
            else:
                print("Already Have 2 Clients")
                client_socket.close()

        else:
            s = notified_socket.recv(1024)
            if s:
                client_name = 'A' if notified_socket == client_A else 'B'
                print(f"Received from {client_name}: {s.decode()}")
                modified = replace_bad_words(s.decode())  # replacing...
                target_client = client_B if notified_socket == client_A else client_A
                if target_client:
                    target_client.send(modified.encode())
                    target_name = 'B' if target_client == client_B else 'A'
                    print(f"To {target_name}: ", modified)

                else:
                    print("A or B is not connected")
            else:
                client_name = 'A' if notified_socket == client_A else 'B'
                print(f"{client_name} disconnected")
                sockets_list.remove(notified_socket)
                if notified_socket == client_A:
                    client_A = None
                else:
                    client_B = None
                notified_socket.close()


    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        if notified_socket == client_A:
            client_A = None
        elif notified_socket == client_B:
            client_B = None
        notified_socket.close()

listener_socket.close()


# Close sockets