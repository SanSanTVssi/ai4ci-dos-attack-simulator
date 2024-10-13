import csv
from datetime import datetime

class CsvLogger:
    def __init__(self, filename='attack_log.csv'):
        """
        Initialize the CSVLogger class with a specified filename.
        By default, it uses 'attack_log.csv'.
        """
        self.filename = filename
        # If the file doesn't exist, create it and add headers
        self.create_file_if_not_exists()

    def create_file_if_not_exists(self):
        """
        Create the CSV file with headers if it doesn't already exist.
        This ensures that the file is structured correctly from the start.
        """
        try:
            with open(self.filename, mode='x', newline='') as file:
                writer = csv.writer(file)
                # Write the headers for the CSV log
                writer.writerow(['timestamp', 'src_ip', 'dst_ip', 'attack_type', 'packet_size'])
        except FileExistsError:
            # If the file already exists, do nothing
            pass

    def log_attack(self, packet_data):
        """
        Log the detected attack packet into the CSV file.
        :param packet_data: A list containing all relevant information about the attack packet.
        """
        with open(self.filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            # Write a new row with the required fields: timestamp, src_ip, dst_ip, attack_type, packet_size
            writer.writerow([
                datetime.fromtimestamp(packet_data[0]).strftime('%d/%m/%Y %H:%M'),  # timestamp
                packet_data[1],                                                     # source IP
                packet_data[2],                                                     # destination IP
                packet_data[3] if len(packet_data) > 3 else 'N/A',                  # type of attack
                packet_data[4] if len(packet_data) > 4 else 'N/A'                   # size of the packet
            ])

