import socket
import threading
from bs4 import BeautifulSoup
from queue import Queue
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[SERVER] - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServerConsumer:
    def __init__(self, host='localhost', port=5000, max_connections=1, output_file="output.txt"):
        self.host = host
        self.port = port
        self.max_connections = max_connections # Max number of concurrent client connections
        self.client_queues = {} # Dictionary to store queues for each connected client
        self.output_file = output_file

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(self.max_connections)
            logger.info(f"Server listening on {self.host}:{self.port}")

            while True:
                client_socket, client_address = server_socket.accept()
                logger.info(f"Connected to client at {client_address}")

                client_queue = Queue()
                self.client_queues[client_address] = client_queue

                # Process tasks for the client
                threading.Thread(
                    target=self.task_processor, args=(client_queue, client_address), daemon=True
                ).start()

                # Handle the client connection
                threading.Thread(
                    target=self.handle_client, args=(client_socket, client_address, client_queue)
                ).start()

    def receive_data(self, client_socket, length):
        # Receive a fixed amount of data from the client
        data = b''
        while len(data) < length:
            packet = client_socket.recv(min(length - len(data), 4096))
            if not packet:
                raise ConnectionError("Connection lost while receiving data.")
            data += packet

        return data.decode('utf-8').strip('\x00')

    def handle_client(self, client_socket, client_address, client_queue):
        try:
            while True:
                data_info = client_socket.recv(4096).decode('utf-8').strip('\x00') 
                if not data_info or data_info == "STOP":
                    logger.info(f"Client at {client_address} disconnected.")
                    break

                try:
                    url, length_of_markup = data_info.strip().split("\n", 1)
                    length_of_markup = int(length_of_markup.strip())
                except ValueError:
                    logger.error(f"Invalid metadata received from {client_address}: {data_info}")
                    continue

                markup = self.receive_data(client_socket, length_of_markup)

                logger.info(f"Received data for {url} (length: {len(markup)})")

                # Add the received data to the client's task queue
                client_queue.put((url, markup))

        except Exception as e:
            logger.error(f"Error handling client {client_address}: {e}")
        finally:
            client_queue.put(None)
            client_socket.close()
            del self.client_queues[client_address]

    def extract_hyperlinks(self, html):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = []

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href'].strip()

                if href.startswith(('http://', 'https://')):
                    links.append(href)

            return links
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return []
        
    def output_result(self, url, hyperlinks):
        output = f"URL: {url}\nLinks:\n"
        output += "\n".join([f"  - {link}" for link in hyperlinks])
        output += "\n\n"

        with open(self.output_file, "a") as file:
            file.write(output)

    def task_processor(self, client_queue, client_address):
        # Process tasks in the client's queue
        while True:
            task = client_queue.get()
            if task is None:
                break

            url, markup = task
            logger.info(f"Processing and saving results for URL: {url}")
            hyperlinks = self.extract_hyperlinks(markup)
            self.output_result(url, hyperlinks)
            client_queue.task_done()

        logger.info(f"All data successfully written to {self.output_file}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--file', type=str, default="output.txt", help="Define output file.")
    parser.add_argument('--host', type=str, default="localhost", help="Host for the server to bind to.")
    parser.add_argument('--port', type=int, default=5000, help="Port for the server to listen on")

    args = parser.parse_args()

    server = ServerConsumer(host=args.host, port=args.port, output_file=args.file)
    server.start()
