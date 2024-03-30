import os

import requests
from bs4 import BeautifulSoup


class Scraper:
    def __init__(self):
        self.download_urls = self.__get_download_urls()

    def __get_download_urls(self):
        response = requests.get("https://wiki.wireshark.org/SampleCaptures")
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a")

        capture_downloads = []

        for link in links:
            try:
                href = link["href"]

                if (
                    href.endswith(".cap")
                    or href.endswith(".pcap")
                    or href.endswith(".pcapng")
                ):
                    capture_downloads.append("https://wiki.wireshark.org" + href)
            except Exception as e:
                print(e)

        return capture_downloads

    def download_captures(self):
        if not os.path.exists(os.path.join(os.getcwd(), "data")):
            os.makedirs(os.path.join(os.getcwd(), "data"))

        for download in self.download_urls:
            response = requests.get(download)
            filename = download.split("/")[-1]
            print("Downloading " + filename)
            with open(os.path.join(os.getcwd(), "data/raw/", filename), "wb") as f:
                f.write(response.content)
