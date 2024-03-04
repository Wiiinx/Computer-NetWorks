import sys
import random
import string
import socket
import select

# Random alphanumeric string. Do not change
def rand_str(l):
    ret = ""
    for i in range(l):
        ret += random.choice(
            string.ascii_lowercase + string.ascii_uppercase + string.digits
        )
    return ret

if (len(sys.argv) > 3) or len(sys.argv) < 2:
    print("Usage: python3 " + sys.argv[0] + " server_port [random_seed]")
    sys.exit(1)

if len(sys.argv) == 3:
    random_seed = int(sys.argv[2])
    random.seed(random_seed)

# TCP socket
server_port = int(sys.argv[1])
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', server_port))

# Listen Mode
server_socket.listen()
print("Listening on port: ", server_port)


while True:
    client_socket, client_address = server_socket.accept()
    print(f"Accepted connection from: {client_address}")
    client_socket.settimeout(30)

    while True:
        data = client_socket.recv(1024).decode()
        if not data:
            break

        print("Received: " + data)
        random_str = rand_str(10)
        new_data = data + random_str
        client_socket.sendall(new_data.encode())
        print(f"Sent: {new_data}")

    client_socket.close()

server_socket.close()
