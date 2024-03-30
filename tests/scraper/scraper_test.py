from unittest import mock

from scraper.scraper import Scraper


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, text):
            self.text = text

    if args[0] == "https://wiki.wireshark.org/SampleCaptures":
        return MockResponse(
            """
            <html>
            <body>
            <a href="capture1.cap">Capture 1</a>
            <a href="capture2.pcap">Capture 2</a>
            <a href="capture3.pcapng">Capture 3</a>
            <a href="capture4.txt">Capture 4</a>
            </body>
            </html>
            """
        )

    return MockResponse(None, 404)


class TestScraper:

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_download_urls(self, mock_get):
        scraper = Scraper()
        assert scraper.download_urls == [
            "https://wiki.wireshark.org/capture1.cap",
            "https://wiki.wireshark.org/capture2.pcap",
            "https://wiki.wireshark.org/capture3.pcapng",
        ]
