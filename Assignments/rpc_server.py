import socket
import sys
import signal


def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def main():
    NUM_TRANSMISSIONS = 10
    if len(sys.argv) < 2:
        print("Usage: python3 " + sys.argv[0] + " server_port")
        sys.exit(1)
    assert len(sys.argv) == 2
    server_port = int(sys.argv[1])

    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_socket.bind(('0.0.0.0', server_port))
    print("Listening on port: ", server_port)


    def cleanup(sig, frame):
        server_socket.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)


    while True:
        rpc_data, client_address = server_socket.recvfrom(1024)
        rpc_data = rpc_data.decode()

        # print(rpc_data)
        n = int(rpc_data.split('(')[1].split(')')[0])
        print("Received:", n)

        result = "yes" if is_prime(n) else "no"
        server_socket.sendto(result.encode(), client_address)

    server_socket.close()


main()



