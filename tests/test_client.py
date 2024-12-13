import unittest
from unittest.mock import MagicMock, patch
import requests

from app.clientProducer import ClientProducer

class TestClientProducer(unittest.TestCase):
    def setUp(self):
        self.client = ClientProducer(host='localhost', port=5000)

    @patch("socket.socket")
    def test_connect_to_server(self, mock_socket):
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        self.client.connect_to_server()
        mock_sock.connect.assert_called_once_with(('localhost', 5000))

    
    @patch("socket.socket")
    def test_disconnect_from_server(self, mock_socket):
        """Test that the client disconnects and sends STOP."""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        self.client.connect_to_server()
        self.client.disconnect_from_server()

        mock_sock.sendall.assert_called_once_with(b"STOP")
        mock_sock.close.assert_called_once()

    @patch("requests.get")
    def test_fetch_url_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_get.return_value = mock_response

        self.client.fetch_url("https://example.com")

        self.assertFalse(self.client.markup_queue.empty())
        url, markup = self.client.markup_queue.get()
        self.assertEqual(url, "https://example.com")
        self.assertEqual(markup, "<html></html>")

    @patch("requests.get")
    def test_fetch_url_failure(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Timeout")

        self.client.fetch_url("https://example.com")

        self.assertTrue(self.client.markup_queue.empty())

    @patch("requests.get")
    def test_fetch_url_incorrect(self, mock_get):
        """Test fetch_url behavior when an incorrect or malformed URL is provided."""
        mock_get.side_effect = requests.exceptions.RequestException("Invalid URL")

        self.client.fetch_url("htp://incorrect-url")

        self.assertTrue(self.client.markup_queue.empty())


        