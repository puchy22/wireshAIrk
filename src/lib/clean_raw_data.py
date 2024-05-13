import os
import shutil

import pyshark

DATASET_PATH = os.path.join(os.getcwd(), "data/raw")


def clean_raw_data(data_path: str = DATASET_PATH) -> None:
    # Create new folder for cleaned data
    try:
        os.mkdir(os.path.join(os.getcwd(), "data/cleaned"))
    except Exception as e:
        print(f"Error creating folder: {e}")

    for file in os.listdir(data_path):
        if file.endswith(".cap") or file.endswith(".pcap") or file.endswith(".pcapng"):
            try:
                cap = pyshark.FileCapture(os.path.join(data_path, file))
                cap.load_packets()
                cap_len = len(cap)
                cap.close()

                # Check the number of packets and if is a network capture
                if cap_len < 1:
                    print(f"File {file} has less than 1 packets. Skipping...")
                    continue
                if cap_len > 125:
                    print(f"File {file} has more than 125 packets. Skipping...")
                    continue

                # Copy file to new folder
                shutil.copyfile(
                    os.path.join(data_path, file),
                    os.path.join(os.getcwd(), "data/cleaned", file),
                )

            except Exception as e:
                print(f"Error with file {file}: {e}")
        else:
            print(f"File {file} is not a pcap file")
