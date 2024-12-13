# WebLinkExtractor

This application facilitates server-client communication to extract and process links from web pages. The application is designed with two main components:

Producer (Client):
- The producer fetches markup from the input URLs.
- It adds the markup to a queue, which acts as the communication medium between the producer and the server.

Consumer (Server):
- The server (consumer) reads the markup data from the queue.
- It processes the markup to extract hyperlinks from the input URLs.

## Setup

Install the required dependencies by running:

```
pip3 install -r requirements.txt
```

## How to Run

### Start the Server
Run the following command to start the server:

```bash
python3 app/serverConstumer.py [-h] [-o FILE] [--host HOST] [--port PORT]
```

```bash
  -h, --help            Show the help message and exit
  -o FILE, --file FILE  Define output file (default: output.txt).
  --host HOST           Host for the server to bind to (default: localhost).
  --port PORT           Port for the server to listen on (default: 5000).
```

### Start the Client
Run the following command to start the client:

```bash
python3 app/clientProducer.py [-h] [-f FILE] [--host HOST] [--port PORT]
```
```bash
  -h, --help            Sho the help message and exit
  -f FILE, --file FILE  Input file containing URLs (one per line).
  --host HOST           Host to bind the server. (default: localhost).
  --port PORT           Port to bind the server. (default: 5000).

```
#### Using Standard Input for Client:

You can also provide the input file via standard input:

```bash
python3 app/clientProducer.py < urls.txt
```

## Usage Example

- Input file: The input file should contain URLs, one per line, such as:

```
https://www.example.com
https://www.python.org
https://www.wikipedia.org
https://www.github.com

```

- Run the Server: Start the server with the following command:

```bash
python3 app/serverConstumer.py
```

- Run the Client: Start the client and provide the input file via standard input:

```bash
python3 app/clientProducer.py < /tests/urls.txt
```

After the execution, the program will create a new output file `output.txt` that might look like this:

```
URL: https://www.example.com
Links:
  - https://www.iana.org/domains/example
  ...
```

- Alternative: Run Test Script You can also use the provided test script to fetch data from urls stored in `tests/urls.txt`:

```
./run.sh
```

## Tests

To run unit tests, use the following command:

```
python3 -m unittest discover tests -v
```

