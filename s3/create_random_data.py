from faker import Faker
import random
from datetime import datetime, timedelta
import pandas as pd
import argparse

fake = Faker()

# BMW profiles (compact, sedan, SUV, performance)
PROFILES = {
    "ID_1": {"model": "BMW 1-series (compact)", "avg_range": (5.5, 8.0), "tank_capacity": 50},
    "ID_2": {"model": "BMW 3-series (sedan)", "avg_range": (6.0, 9.5), "tank_capacity": 60},
    "ID_3": {"model": "BMW X5 (SUV)", "avg_range": (8.5, 12.5), "tank_capacity": 85},
    "ID_4": {"model": "BMW M-series (performance)", "avg_range": (10.0, 16.0), "tank_capacity": 68},
}

def generate_bmw_telemetry(num_records=20, start_time=None, interval_minutes=15):
    """Generate random BMW IoT telemetry records using Faker."""
    if start_time is None:
        start_time = datetime.utcnow()

    records = []
    timestamp = start_time
    device_ids = list(PROFILES.keys())

    for i in range(num_records):
        did = random.choice(device_ids)
        profile = PROFILES[did]

        # Random odometer (5k–300k km depending on profile)
        odometer = random.randint(5_000, 300_000)
        # Trip distance (short to medium trips)
        trip_km = round(random.uniform(2, 80), 1)

        # Fuel consumption realistic to profile
        avg_cons = round(random.uniform(*profile["avg_range"]), 2)
        instant_cons = round(random.uniform(avg_cons - 2, avg_cons + 2), 2)
        instant_cons = max(3.0, instant_cons)  # safety lower bound

        # Fuel level (%)
        fuel_percent = round(random.uniform(10, 100), 1)

        record = {
            "timestamp": timestamp.isoformat(),
            "device_id": did,
            "model": profile["model"],
            "odometer_km": odometer,
            "trip_driven_km": trip_km,
            "instant_consumption_l_per_100km": instant_cons,
            "avg_consumption_l_per_100km": avg_cons,
            "fuel_level_percent": fuel_percent,
            "location": fake.location_on_land()[2:],  # country, region, city
        }
        records.append(record)

        # Increment time
        timestamp += timedelta(minutes=interval_minutes)

    return records

# Example usage:
if __name__ == "__main__":
    DIRECTORY = "./files/"
    
    args = argparse.ArgumentParser()
    args.add_argument("--file-format", type=str, default="JSON", help="File format: JSON or CSV")
    args.add_argument("--file-number",type=int, default=1,help="Declare the number of files to generate")
    args = args.parse_args()
    print(args.file_number)
    if args.file_format.upper() == "JSON":
        for i in range(args.file_number):
            data = generate_bmw_telemetry()
            df = pd.DataFrame.from_dict(data)
            file_name =f"generated_data_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{i}.jsonl"
            print(f"File name is:{file_name} ")
            df.to_json(DIRECTORY+file_name, orient="records", lines=True)
    elif args.file_format.upper() == "CSV":
        for i in range(args.file_number):       
            data = generate_bmw_telemetry()     
            df = pd.DataFrame.from_dict(data)
            file_name =f"generated_data_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_{i}.csv"
            print(f"File name is:{file_name} ")
            df.to_csv(DIRECTORY+file_name)
    else:
        print("Unsupported file type. Please choose JSON or CSV.")


