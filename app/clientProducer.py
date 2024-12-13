import threading
import queue
import requests
import argparse
import sys
import socket
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[CLIENT] - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClientProducer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.markup_queue = queue.Queue() # Queue to hold fetched URL markups
        self.client_socket = None  # Socket for server communication
        self.buffer_size = 4096

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            logger.info(f"Connected to server at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Error connecting to server: {e}")
            raise

    def disconnect_from_server(self):
        if self.client_socket:
            try:
                self.client_socket.sendall("STOP".encode('utf-8'))
                self.client_socket.close()
                logger.info("Disconnected from server.")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")

    def fetch_url(self, url):
        try:
            logger.info(f"Fetching URL: {url}")
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            markup = response.text
            logger.info(f"Fetched markup for {url} (length: {len(markup)})")

            # Add the result to the queue
            self.markup_queue.put((url, markup))
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")

    def send_aligned_data(self, sock, data, buffer_size=4096):
        "Ensure data alignment to avoid sending issues"
        total_sent = 0
        data_length = len(data)

        # Align the data
        padding_length = (buffer_size - (data_length % buffer_size)) % buffer_size
        data += b'\0' * padding_length 

        while total_sent < len(data):
            chunk = data[total_sent:total_sent + buffer_size]
            sent = sock.send(chunk)
            if sent == 0:
                raise RuntimeError("Socket connection broken")

            total_sent += sent

    def send_from_queue(self):
        # Continuously send data from the queue to the server
        while True:
            try:
                task = self.markup_queue.get()
                if task is None:
                    break

                url, markup = task
                data_markup = markup.encode('utf-8')

                # Calculate the aligned data size
                length_of_markup = len(data_markup)
                padded_size = length_of_markup + (self.buffer_size - (length_of_markup % self.buffer_size)) % self.buffer_size

                logger.info(f"Sending data for {url} to server.")
                data_info = f"{url}\n{padded_size}".encode('utf-8')
                self.send_aligned_data(self.client_socket, data_info)

                data_markup = f"{markup}".encode('utf-8')
                self.send_aligned_data(self.client_socket, data_markup)

            except Exception as e:
                logger.error(f"Error sending data to server: {e}")

    def send_to_server(self, urls):
        try:
            self.connect_to_server()

            consumer_thread = threading.Thread(target=self.send_from_queue, daemon=True)
            consumer_thread.start()

            threads = []
            for url in urls:
                thread = threading.Thread(target=self.fetch_url, args=(url,))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

            # Signal to stop sending data to server
            self.markup_queue.put(None)
            consumer_thread.join()

        finally:
            self.disconnect_from_server()


def read_urls_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            urls = [line.strip() for line in file if line.strip()]
        return urls

    except FileNotFoundError:
        logger.error(f"Error: File '{file_path}' not found.")
        sys.exit(1)

def read_urls_from_stdin():
    input_data = sys.stdin.read()

    urls = [line.strip() for line in input_data.splitlines() if line.strip()]
    return urls


if __name__ == "__main__":

    # Parse arguments
    parser = argparse.ArgumentParser(description="Process URLs for link extraction.")
    parser.add_argument('-f', '--file', type=str, help="File containing URLs (one per line).")
    parser.add_argument('--host', type=str, default="localhost", help="Host to bind the server.")
    parser.add_argument('--port', type=int, default=5000, help="Port to bind the server.")

    args = parser.parse_args()

    if args.file:
        urls = read_urls_from_file(args.file)

    else:
        if sys.stdin.isatty():
            logger.error("No file specified and no input from stdin.")
            sys.exit(1)
        urls = read_urls_from_stdin()

    client = ClientProducer(host=args.host, port=args.port)
    client.send_to_server(urls)
