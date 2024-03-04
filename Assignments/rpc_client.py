import socket
import sys
import random
NUM_TRANSMISSIONS = 10


# python3 rpc ̇client.py 127.0.0.1 9001
def main():
    if len(sys.argv) > 4 or len(sys.argv) < 3:
        print("Usage: python3 " + sys.argv[0] + " server_address server_port [random_seed]")
        sys.exit(1)

    if len(sys.argv) == 4:
        random_seed = int(sys.argv[3])
        random.seed(random_seed)

    server_address = sys.argv[1]
    server_port = int(sys.argv[2])


    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    for i in range(NUM_TRANSMISSIONS):
        data = random.randint(0, 100)
        request = "prime(" + str(data) + ")"
        print("sent: " + request)

        client_socket.sendto(request.encode(), (server_address, server_port))
        response, addr = client_socket.recvfrom(1024)
        print("prime: " + response.decode())

    client_socket.close()

main()


