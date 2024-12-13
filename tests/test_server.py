import unittest

from app.serverConsumer import ServerConsumer

class TestServerConsumer(unittest.TestCase):
    def setUp(self):
        self.server = ServerConsumer(host='localhost', port=5001)

    def test_extract_hyperlinks(self):
        html = """
        <html>
            <head><title>Test</title></head>
            <body>
                <a href="https://example.com">Example</a>
                <a href="https://test.com">Test</a>
                <a href="/relative/path">Relative Path</a>
                <a href="javascript:void(0);">Invalid Link</a>
                <a href="#">Empty Fragment</a>
            </body>
        </html>
        """

        hyperlinks = self.server.extract_hyperlinks(html)

        expected_hyperlinks = [
            "https://example.com",
            "https://test.com"
        ]

        self.assertEqual(hyperlinks, expected_hyperlinks)

    def test_extract_hyperlinks_empty_html(self):
        html = ""
        hyperlinks = self.server.extract_hyperlinks(html)
        self.assertEqual(hyperlinks, [])

    def test_extract_hyperlinks_no_links(self):
        html = "<html><head><title>Test</title></head><body>No links here!</body></html>"
        hyperlinks = self.server.extract_hyperlinks(html)
        self.assertEqual(hyperlinks, [])

if __name__ == "__main__":
    unittest.main()
