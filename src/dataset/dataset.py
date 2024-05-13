import json
import os
import re
from subprocess import check_output

import pyshark


class Dataset:
    def __init__(self, data_path: str):
        self.__questions = [
            "What is the total number of packets in the trace?",
            "How many unique communicators are present in the trace?",
            "What is the IP that participates the most in communications in the trace?",
            "What is the total size of transmitted bytes?",
            "What is the average size of packets in bytes?",
            "What predominates in the capture the use of ICMP, TCP or UDP?",
            "How long in seconds does the communication last?",
            "What is the average of packets sent per second?",
            "What is the average bytes/s sent in the communication?",
        ]

        if os.path.exists(os.path.join(os.getcwd(), data_path)):
            self.__data_path = data_path
            self.__files = self.__get_files(data_path)
        else:
            raise Exception("The path is not valid")

    def answer_questions_for_cap(self, file: str) -> str:
        cap = pyshark.FileCapture(os.path.join(self.__data_path, file))
        quest_sol = {}

        num_packets = 0
        num_bytes = 0
        ip_count = {}
        protocols_count = {}
        start_timestamp = 0

        can_answer_ip_question = False

        for packet in cap:
            try:
                # Get Basic info
                if num_packets == 0:
                    start_timestamp = float(packet.sniff_timestamp)

                num_packets += 1
                num_bytes += int(packet.length)

                for layer in packet.layers:
                    if layer.layer_name not in protocols_count:
                        protocols_count[layer.layer_name] = 1
                    else:
                        protocols_count[layer.layer_name] += 1

                # IP layer
                if "ip" in packet and packet.ip.src and packet.ip.dst:
                    can_answer_ip_question = True
                    ip_src = packet.ip.src
                    ip_dst = packet.ip.dst
                elif "ipv6" in packet and packet.ipv6.src and packet.ipv6.dst:
                    can_answer_ip_question = True
                    ip_src = packet.ipv6.src
                    ip_dst = packet.ipv6.dst
                else:
                    continue

                if ip_src not in ip_count:
                    ip_count[ip_src] = 1
                else:
                    ip_count[ip_src] += 1

                if ip_src != ip_dst:
                    if ip_dst not in ip_count:
                        ip_count[ip_dst] = 1
                    else:
                        ip_count[ip_dst] += 1

            except Exception as e:
                print(e)

        cap.close()

        communication_time = round(float(packet.sniff_timestamp) - start_timestamp, 6)

        bytes_per_second = (
            num_bytes / communication_time if communication_time > 0 else 0
        )

        for i, question in enumerate(self.__questions):
            if i == 0:
                quest_sol[question] = (
                    f"In the capture there are a total of {str(num_packets)} packets"
                )
            elif i == 1:
                if can_answer_ip_question:
                    quest_sol[question] = (
                        f"There are a total of {str(len(ip_count))} unique communicators in the trace. These are the IPs: {', '.join(ip_count.keys())}"
                    )
                else:
                    quest_sol[question] = (
                        "The used protocol in the capture does not have IP addresses. Cannot answer the question."
                    )
            elif i == 2:
                if can_answer_ip_question:
                    quest_sol[question] = (
                        f"The IP that participates the most in the communication is the IP {max(ip_count, key=ip_count.get)} this appears in a total of {ip_count[max(ip_count, key=ip_count.get)]} communications."
                    )
                else:
                    quest_sol[question] = (
                        "The used protocol in the capture does not have IP addresses. Cannot answer the question."
                    )
            elif i == 3:
                quest_sol[question] = (
                    f"The total size of transmitted bytes is {str(num_bytes)}."
                )
            elif i == 4:
                quest_sol[question] = (
                    f"The average size of packets in bytes is {str(int(num_bytes / num_packets))} bytes."
                )
            elif i == 5:
                icmp = protocols_count.get("icmp", 0)
                icmpv6 = protocols_count.get("icmpv6", 0)
                tcp = protocols_count.get("tcp", 0)
                udp = protocols_count.get("udp", 0)

                if icmp == icmpv6 == tcp == udp == 0:
                    quest_sol[question] = (
                        "In the capture is not used any of those protocols."
                    )
                elif icmp > icmpv6 and icmp > tcp and icmp > udp:
                    quest_sol[question] = "In the capture predominates the use of ICMP."
                elif icmpv6 > icmp and icmpv6 > tcp and icmpv6 > udp:
                    quest_sol[question] = (
                        "In the capture predominates the use of ICMPv6."
                    )
                elif tcp > icmp and tcp > icmpv6 and tcp > udp:
                    quest_sol[question] = "In the capture predominates the use of TCP."
                elif udp > icmp and udp > icmpv6 and udp > tcp:
                    quest_sol[question] = "In the capture predominates the use of UDP."
                else:
                    quest_sol[question] = (
                        "In the capture is not used any of those protocols."
                    )
            elif i == 6:
                quest_sol[question] = (
                    f"The communication lasts {str(communication_time)} seconds."
                )
            elif i == 7:
                quest_sol[question] = (
                    f"The average of packets sent per second is {str(round(bytes_per_second, 2))}."
                )
            elif i == 8:
                quest_sol[question] = (
                    f"The average bytes/s sent in the communication is {str(round(bytes_per_second, 2))}."
                )

        return quest_sol

    def generate_dataset(self, name: str, context: str) -> None:
        """Generate a dataset with all the questions for each file"""
        if not os.path.exists(os.path.join(os.getcwd(), f"data/{name}/")):
            os.makedirs(os.path.join(os.getcwd(), f"data/{name}/"))

        # Create a json file where store the dataset
        with open(os.path.join(os.getcwd(), f"data/{name}/dataset.jsonl"), "w") as f:
            for file_cap in self.__files:
                print(f"Answering questions for {file_cap}")
                try:
                    # Answer the question
                    question_and_answers = self.answer_questions_for_cap(file_cap)

                    i = 0

                    for question, answer in question_and_answers.items():
                        prompt = f"{context[i]}\nNo.|Time|Source|Destination|Protocol|Length|Info\n {self.__cap_to_str(os.path.join(self.__data_path, file_cap))}\nQ: {question}"

                        data = {
                            "context": "You are a network analyst and you have to help answering questions about a network trace.",
                            "prompt": prompt,
                            "answer": answer,
                        }

                        f.write(json.dumps(data) + "\n")
                        i += 1
                except Exception as e:
                    print(f"Error generating dataset for {file_cap}. ERROR: {e}")
                    import sys

                    sys.exit(1)

    def __get_files(self, data_path: str) -> list:
        files = []
        for file in os.listdir(data_path):
            if (
                file.endswith(".cap")
                or file.endswith(".pcap")
                or file.endswith(".pcapng")
            ):
                files.append(file)
        return files

    def __cap_to_str(self, file: str) -> str:
        try:
            out = check_output(
                [
                    "tshark",
                    "-r",
                    file,
                    "-T",
                    "tabs",
                ]
            )
            return self.__clean_cap_format(out.decode("utf-8"))
        except Exception as e:
            raise Exception(f"Fail reading the file. ERROR: {e}")

    def __clean_cap_format(self, cap: str) -> str:
        # Split the string by lines
        cap_lines = cap.strip().split("\n")

        match_tabs = r"(?<!\\)\t"

        table_rows = []

        for line in cap_lines:
            columns = re.split(match_tabs, line.strip())

            if "\u2192" in columns:
                # Remove it from list
                columns.remove("\u2192")

            # Format columns elements before append them to the table
            for i, col in enumerate(columns):
                col = col.strip().replace("\u2192", "->").replace('"', "'")
                columns[i] = col

            table_rows.append(columns)

        cap_formated = ""

        for row in table_rows:
            cap_formated += " | ".join(row) + "\n"

        return cap_formated

    def get_questions(self):
        return self.__questions
