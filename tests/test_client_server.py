import unittest
from unittest.mock import patch, call, MagicMock
from app.clientProducer import ClientProducer
from app.serverConsumer import ServerConsumer
import queue
import os
import threading

class TestClientServerIntegration(unittest.TestCase):
    
    @patch("socket.socket")
    def test_client_server_interaction(self, mock_socket):
        mock_server_sock = MagicMock()
        mock_socket.return_value = mock_server_sock

        server = ServerConsumer(host='localhost', port=5001)
        client = ClientProducer(host='localhost', port=5001)

        # Set queues
        mock_server_queue = queue.Queue()
        server.client_queues = {('127.0.0.1', 5001): mock_server_queue}

        markup = "<html><a href='https://link.com'>Link</a></html>"
        markup_encoded = markup.encode('utf-8')
        url = "https://example.com"
        metadata = f"{url}\n{len(markup_encoded)}".encode('utf-8')

        mock_server_sock.recv.side_effect = [
            metadata, 
            markup_encoded, 
            b''         
        ]

        with patch.object(client, "send_aligned_data") as mock_send_aligned_data:
            client.connect_to_server()
            client.markup_queue.put((url, markup))
            client.markup_queue.put(None)
            client.send_from_queue()
            
            self.assertEqual(mock_send_aligned_data.call_count, 2)
        
        with patch.object(server, "receive_data", wraps=server.receive_data) as mock_receive_data:
            
            server.handle_client(mock_server_sock, ('127.0.0.1', 5001), mock_server_queue)

            mock_receive_data.assert_called()
            self.assertFalse(mock_server_queue.empty())

            if not mock_server_queue.empty():
                url, html_markup = mock_server_queue.get()
                self.assertEqual(url, "https://example.com")
                self.assertIn("<a href='https://link.com'>", html_markup)


    

    





        

