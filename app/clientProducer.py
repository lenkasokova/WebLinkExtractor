import threading
import queue
import requests
import argparse
import sys
import queue
import socket

class ClientProducer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.markup_queue = queue.Queue()
        self.client_socket = None

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
        except Exception as e:
            print(f"Error connecting to server: {e}")
            raise

    def disconnect_from_server(self):
        if self.client_socket:
            try:
                self.client_socket.sendall("STOP".encode('utf-8'))
                self.client_socket.close()
                print("Disconnected from server.")
            except Exception as e:
                print(f"Error during disconnect: {e}")

    def fetch_url(self, url):
        try:
            print(f"Fetching URL: {url}")
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            markup = response.text
            print(f"Fetched markup for {url} (length: {len(markup)})")

            # Add the result to the queue
            self.markup_queue.put((url, markup))
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    def send_aligned_data(self, sock, data, buffer_size=4096):
        total_sent = 0
        data_length = len(data)

        # Aligned the data
        padding_length = (buffer_size - (data_length % buffer_size)) % buffer_size
        data += b'\0' * padding_length 

        while total_sent < len(data):
            chunk = data[total_sent:total_sent + buffer_size]
            sent = sock.send(chunk)
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            
            total_sent += sent

    def send_from_queue(self):
         while True:
            try:
                task = self.markup_queue.get()
                if task is None:
                    break

                url, markup = task
                data_markup = markup.encode('utf-8')

                length_of_markup = len(data_markup)
                buffer_size = 4096
                padded_size = length_of_markup + (buffer_size - (length_of_markup % buffer_size)) % buffer_size

                print(f"Sending data for {url} to server.")
                data_info = f"{url}\n{padded_size}".encode('utf-8')
                self.send_aligned_data(self.client_socket, data_info)
                

                data_markup = f"{markup}".encode('utf-8')
                self.send_aligned_data(self.client_socket, data_markup)
            
            except Exception as e:
                print(f"Error sending data to server: {e}")

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
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

def read_urls_from_stdin():
    input_data = sys.stdin.read()

    urls = [line.strip() for line in input_data.splitlines() if line.strip()]
    return urls


if __name__ == "__main__":

    # parse argument
    parser = argparse.ArgumentParser(description="Process URLs for link extraction.")
    parser.add_argument('-f', '--file', type=str, help="File containing URLs (one per line).")
    parser.add_argument('--host', type=str, default="localhost", help="Host to bind the server.")
    parser.add_argument('--port', type=int, default=5000, help="Port to bind the server.")
    
    args = parser.parse_args()

    if args.file:
        urls = read_urls_from_file(args.file)
    
    else:
        if sys.stdin.isatty():
            print("No file specified and no input from stdin.")
            sys.exit(1)
        urls = read_urls_from_stdin()

    client = ClientProducer(host=args.host, port=args.port)
    client.send_to_server(urls)