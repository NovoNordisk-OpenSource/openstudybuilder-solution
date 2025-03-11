import socket
import sys
import threading
import time


class NetworkSimulator:
    def __init__(self, host, port, server_port, latency=0.005):
        # Connect to the external TCP service

        self.server_host = host
        self.server_port = port
        self.latency = latency

        # Create a raw TCP server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("localhost", server_port))
        self.server_socket.listen(100)
        self.active = True
        self.nbr_requests = 0
        self.nbr_replies = 0
        self.requests_bytes = 0
        self.replies_bytes = 0

        self.running = True
        print(f"Server listening on port {server_port}...")

    def log_stats(self):
        prev_requests = self.nbr_requests
        while self.running:
            time.sleep(1)
            if self.nbr_requests != prev_requests:
                prev_requests = self.nbr_requests
                self.print_stats()

    def print_stats(self):
        print(
            f"Requests, nbr: {self.nbr_requests}, bytes: {self.requests_bytes}. Replies, nbr: {self.nbr_replies}, bytes: {self.replies_bytes}"
        )

    def forward(self, source_socket, dest_socket, is_request):
        while self.running:
            # Forward requests from client to external service
            try:
                data = source_socket.recv(4096)
                data_size = len(data)
                if data_size > 0:
                    time.sleep(self.latency)
                    if is_request:
                        self.nbr_requests += 1
                        self.requests_bytes += data_size
                    else:
                        self.nbr_replies += 1
                        self.replies_bytes += data_size
                    dest_socket.sendall(data)
                else:
                    print("Zero bytes, closing connection, request: ", is_request)
                    break
            except (ConnectionResetError, OSError, BrokenPipeError):
                print("Got exception, closing connection, request: ", is_request)
                break
        source_socket.close()

    def wait_for_connection(self):
        while self.running:
            # Accept client connection
            print("------ Waiting for client connection...")
            client_socket, client_address = self.server_socket.accept()
            print(f"------ Accepted connection from {client_address}")
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((self.server_host, self.server_port))
            threading.Thread(
                target=self.forward,
                args=(client_socket, server_socket, True),
                daemon=True,
            ).start()
            threading.Thread(
                target=self.forward,
                args=(server_socket, client_socket, False),
                daemon=True,
            ).start()
        print("Shutting down server...")

    def run(self):
        logger = threading.Thread(target=self.log_stats, daemon=True)
        logger.start()
        server = threading.Thread(target=self.wait_for_connection, daemon=True)
        server.start()
        while True:
            try:
                user_input = input(
                    "Give a new delay in milliseconds, 'p' to print stats now, 'r' to reset counters, or 'q' to exit: "
                )
                if user_input == "q":
                    print("Exiting...")
                    self.running = False
                    self.server_socket.close()
                    break
                elif user_input == "r":
                    print("Resetting counters...")
                    self.nbr_requests = 0
                    self.nbr_replies = 0
                    self.requests_bytes = 0
                    self.replies_bytes = 0
                elif user_input == "p":
                    self.print_stats()
                elif user_input != "":
                    try:
                        requested_delay = float(user_input)
                        self.latency = requested_delay / 1000.0
                        print(f"Set delay to {requested_delay} milliseconds.")
                    except ValueError:
                        print("Invalid input:", user_input)
            except KeyboardInterrupt:
                print("Exiting...")
                self.running = False
                self.server_socket.close()
                break
        logger.join()
        server.join()
        print("Server stopped.")


def main():
    args = sys.argv
    if len(args) < 2:
        print(
            "Start a server that acts as a middleman between a service and a client, with a given latency in milliseconds."
        )
        print(
            "Usage: python networksimulator.py <service_host> <service_port> <server_port> <latency>"
        )
        sys.exit(1)
    service_host = args[1]
    service_port = int(args[2])
    serve_on_port = int(args[3])
    latency = float(args[4])

    sim = NetworkSimulator(
        service_host, service_port, serve_on_port, latency=latency / 1000.0
    )
    sim.run()


if __name__ == "__main__":
    main()
