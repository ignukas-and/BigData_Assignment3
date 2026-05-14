from pymongo import MongoClient
import csv
import multiprocessing
from datetime import datetime
import matplotlib.pyplot as plt

# options
chunk_size = 20000
num_of_processes = 11
client_url = "mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=rs0"

# files
input_file = "aisdk-2026-01-01.csv"

dir_input = "../input/"
dir_output = "../output/"


def insert_data(rows):
    client = MongoClient(
    client_url,
    retryWrites=True,
    retryReads=True
)

    collection = client["vessels"]["all_data"]

    clean_rows = []
    for row in rows:

        clean_row = {k.replace("# Timestamp", "Timestamp"): v for k, v in row.items()}

        clean_row['Timestamp'] = datetime.strptime(clean_row['Timestamp'], "%d/%m/%Y %H:%M:%S")

        clean_rows.append(clean_row)

    collection.insert_many(clean_rows, ordered=False)

    client.close()

def noise_filtering(mmsi):
    client = MongoClient(
    client_url,
    retryWrites=True,
    retryReads=True
    )

    db = client["vessels"]
    collection_filtered = client["vessels"]["filtered_data"]
    collection_time_diffs = client["vessels"]["vessel_time_diffs"]

    correct_mmsi = mmsi.isdigit() and len(mmsi) == 9
    # cargo type is not added on purpose
    if correct_mmsi:
        missing_criteria = [None, "Undefined", "Unknown", "Unknown value"]
        clean_data = list(db.all_data.find({
            "MMSI": mmsi,
            "Type of mobile": {"$exists": True, "$nin": missing_criteria},
            "Latitude": {"$exists": True, "$ne": None},
            "Longitude": {"$exists": True, "$ne": None},
            "Navigational status": {"$exists": True, "$nin": missing_criteria},
            "ROT": {"$exists": True, "$nin": missing_criteria},
            "SOG": {"$exists": True, "$nin": missing_criteria},
            "COG": {"$exists": True, "$nin": missing_criteria},
            "Heading": {"$exists": True, "$nin": missing_criteria},
            "IMO": {"$exists": True, "$nin": missing_criteria},
            "Callsign": {"$exists": True, "$nin": missing_criteria},
            "Name": {"$exists": True, "$nin": missing_criteria},
            "Ship type": {"$exists": True, "$nin": missing_criteria},
            "Width": {"$exists": True, "$nin": missing_criteria},
            "Length": {"$exists": True, "$nin": missing_criteria},
            "Type of position fixing device": {"$exists": True, "$nin": missing_criteria},
            "Draught": {"$exists": True, "$nin": missing_criteria},
            "Destination": {"$exists": True, "$nin": missing_criteria},
            "ETA": {"$exists": True, "$nin": missing_criteria},
            "Data source type": {"$exists": True, "$nin": missing_criteria},
            "A": {"$exists": True, "$nin": missing_criteria},
            "B": {"$exists": True, "$nin": missing_criteria},
            "C": {"$exists": True, "$nin": missing_criteria},
            "D": {"$exists": True, "$nin": missing_criteria}
        }).sort("Timestamp", 1))

        if len(clean_data) >= 100:
            collection_filtered.insert_many(clean_data, ordered=False)

            # time difference calculation
            time_diffs = []
            for i in range(1, len(clean_data)):
                a_t = clean_data[i]['Timestamp']
                a_t_1 = clean_data[i - 1]['Timestamp']

                time_diffs.append(a_t - a_t_1)

            time_diffs = [d.total_seconds() for d in time_diffs]
            for_ins_time_diffs = [{"timediff": diff} for diff in time_diffs]
            collection_time_diffs.insert_many(for_ins_time_diffs, ordered=False)

    client.close()

def print_plot(client_url, dir_output):
    client = MongoClient(
    client_url,
    retryWrites=True,
    retryReads=True
    )
    db = client["vessels"]

    time_diffs = list(db.vessel_time_diffs.find({}))
    diffs = [time_diffs[i]['timediff'] for i in range(1, len(time_diffs))]

    plt.hist(diffs, bins=30, color='skyblue', edgecolor='black')

    # Adding labels and title
    plt.xlabel('Time Difference (Seconds)')
    plt.ylabel('Frequency')
    plt.title('Time Difference Histogram')

    plt.savefig(dir_output + 'time_diff_hist.png', dpi=300)

    client.close()

if __name__ == "__main__":
    print("Preparing...")
    input_file_path = dir_input + input_file
    with open(input_file_path) as f:
        reader = list(csv.DictReader(f))
    chunks = [
        reader[i:i + chunk_size]
        for i in range(0, len(reader), chunk_size)
    ]
    unique_mmsi = list({row["MMSI"] for row in reader})

    print("Preparing indexes...")
    client = MongoClient(
        client_url,
        retryWrites=True,
        retryReads=True
    )
    db = client["vessels"]
    db.all_data.create_index("MMSI")
    client.close()

    print("Uploading data...")
    pool = multiprocessing.Pool(processes=num_of_processes)
    pool.map(insert_data, chunks)
    pool.close()

    print("Preparing indexes to filtered data...")
    client = MongoClient(
        client_url,
        retryWrites=True,
        retryReads=True
    )
    db = client["vessels"]
    db.filtered_data.create_index("MMSI")
    client.close()

    print("Filtering data...")
    pool = multiprocessing.Pool(processes=num_of_processes)
    pool.map(noise_filtering, unique_mmsi)
    pool.close()

    print("Generating plot...")
    print_plot(client_url, dir_output)

    print("Done!")

