#!./.venv/bin/python

import logging
import os
import pwd
import psutil
import socket
import subprocess
import re
import time
from datetime import datetime

import yaml
import distro
import requests
from pymongo import MongoClient
from pymongo.errors import BulkWriteError, DuplicateKeyError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load credentials from a YAML file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Connect to MongoDB
client = MongoClient(config["mongo_uri"])
db = client[config["database_name"]]

def convert_to_kilobytes(value):
    # Convert bytes to kilobytes
    return f"{value // 1024}"

def get_local_ip(interface_name):
    addresses = psutil.net_if_addrs()
    if interface_name in addresses:
        for address in addresses[interface_name]:
            if address.family == socket.AF_INET:
                return address.address
    return None

def get_hostname():
    return socket.gethostname()

def get_kernel_info():
    return {
        "Kernel Version": os.uname().release,
        "System Name": os.uname().sysname,
        "Node Name": os.uname().nodename,
        "Machine": os.uname().machine
    }

def get_operating_system_info():
    os_info = {
        "distribution": distro.name(),
        "version": distro.version(),
    }
    return os_info

def check_for_updates():
    os_info = get_operating_system_info()
    update_available = False

    if os_info["distribution"] in ["ubuntu", "debian"]:
        # Customize the URL based on your distribution
        update_url = "https://changelogs.ubuntu.com/meta-release"
        response = requests.get(update_url)

        if response.status_code == 200:
            latest_version = response.text.split("\n")[2].split("=")[1]
            current_version = os_info["version"]

            # Compare versions to check for updates
            update_available = latest_version > current_version

    return {
        "Update available": update_available,
    }

def get_cpu_info():
    return {
        "Physical Cores": psutil.cpu_count(logical=False),
        "Total Cores": psutil.cpu_count(logical=True),
        "Processor Speed": int(psutil.cpu_freq().current),
        #"Cpu_usage_per_core": dict(enumerate(psutil.cpu_percent(percpu=True, interval=1))),
        "Total Cpu Usage": int(psutil.cpu_percent(interval=1))
    }

def get_memory_info():
    memory_info = psutil.virtual_memory()
    # Convert memory values to kilobytes
    return {
        "Memory (total)": int(memory_info.total / 1024),
        "Memory (used)": int(memory_info.used / 1024),
        "Memory (free)": int(memory_info.free / 1024),
    }

def get_disk_info():
    disk_info = psutil.disk_usage('/')
    # Convert disk values to kilobytes
    return {
        "Disk (total)": int(disk_info.total / 1024),
        "Disk (used)": int(disk_info.used / 1024),
        "Disk (free)": int(disk_info.free / 1024),
    }

def get_net_io_counters():
    io_counters = psutil.net_io_counters()
    return {
        "Bytes Sent": io_counters.bytes_sent,
        "Bytes Recv": io_counters.bytes_recv,
        "Packets Sent": io_counters.packets_sent,
        "Packets Recv": io_counters.packets_recv,
        # "errin": io_counters.errin,
        # "errout": io_counters.errout,
        # "dropin": io_counters.dropin,
        # "dropout": io_counters.dropout
    }

def get_system_uptime():
    boot_time_timestamp = psutil.boot_time()
    current_time_timestamp = time.time()
    uptime_seconds = current_time_timestamp - boot_time_timestamp
    uptime_minutes = uptime_seconds // 60
    uptime_hours = uptime_minutes // 60
    uptime_days = uptime_hours // 24
    uptime_str = f"{int(uptime_days)} days, {int(uptime_hours % 24)} hours, {int(uptime_minutes % 60)} minutes, {int(uptime_seconds % 60)} seconds"
    return {"Uptime": uptime_str}


def get_temperature_info():
    temperature_data = {"CPU": None, "Disk(sda)": None, "Disk(NVMe0)": None}

    try:
        # Get temperature for the CPU
        cpu_temperatures = psutil.sensors_temperatures()
        if "coretemp" in cpu_temperatures:
            for temp in cpu_temperatures["coretemp"]:
                if temp.label == 'Package id 0':
                    temperature_data["CPU"] = temp.current

        # Disk temperatures for disk vary if hdd,sdd,nvme,etc. adjust as needed, disktemp.sh script can help
        # disk temperatures need more detection work.
        specific_disk = 'sda'
        disk_temperature_output = disk_temperature_output = subprocess.run(['disktemp.sh', f'/dev/{specific_disk}'], capture_output=True, text=True).stdout
        temperature_data[f"Disk({specific_disk})"] = int(disk_temperature_output)

        # Get NVMe temperatures
        nvme_temperatures = psutil.sensors_temperatures()
        if "nvme" in nvme_temperatures:
            nvme_sensors = nvme_temperatures["nvme"]
            # Iterate through NVMe sensors 
            for sensor in nvme_sensors:
                # Choose the temperature for the desired sensors ("Sensor 1" and "Sensor 2")
                if sensor.label == 'Sensor 1':
                    temperature_data["Disk(NVMe0)"] = int(sensor.current)

    except Exception as e:
        print(f"An error occurred: {e}")

    return temperature_data

def count_users():
    # Get all user entries
    all_users = pwd.getpwall()

    # Filter out system users based on UID threshold (1000 in this example) and exclude "nobody" user
    created_users = [user for user in all_users if user.pw_uid >= 1000 and user.pw_name != "nobody"]

    # Get the usernames of created users
    user_names = [user.pw_name for user in created_users]

    # Count total created users
    total_users = len(user_names)

    # Get currently connected users
    connected_users = subprocess.run(['who'], capture_output=True, text=True).stdout.split('\n')
    connected_users = [user.split()[0] for user in connected_users if user]

    # Get the usernames of active users
    active_user_names = list(set(connected_users))

    # Count active users
    active_users = len(active_user_names)

    return {
        "Total users:": total_users,
        "Usernames:": user_names,
        "Active user": active_users,
    }

def list_active_connections():
    try:
        # Run the ss command to list active connections
        result = subprocess.run(['ss', '-t', '-u', '-p', '-a', '-n'], capture_output=True, text=True, check=True)
        output = result.stdout

        # Split the output by lines and remove empty lines
        lines = output.split('\n')
        lines = [line.strip() for line in lines if line.strip()]

        # Extract the description (first line)
        description = lines[0]

        # Exclude the first line (description)
        lines = lines[1:]

        # Return the description and the list of active connections
        return {
            "Number active connections": len(lines),
            "Description": description,
            "List active connections": lines
        }
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None, None


def get_system_info():
    local_ip = get_local_ip('wg0')
    hostname = get_hostname().upper()
    hostname_short = "Server_one" #Custom name if needed
    timestamp = int(datetime.now().timestamp() * 1e6)

    system_data = {
        "hostcharts": [
            {"_id": 1, "Title": "Cpu Info"},
            {"_id": 2, "Title": "Memory Info"},
            {"_id": 3, "Title": "Disk Info"},
            {"_id": 4, "Title": "Kernel Info"},
            {"_id": 5, "Title": "Network Info"},
            {"_id": 6, "Title": "System Uptime"},
            {"_id": 7, "Title": "Temperature Info"},
            {"_id": 8, "Title": "Update Available"},
            {"_id": 9, "Title": "Users"},
            {"_id": 10, "Title": "Connections"},
        ],
        "hostreports": [
            {"chart": 1, "hostserver": local_ip, "ts": timestamp, "hostreport": get_cpu_info()},
            {"chart": 2, "hostserver": local_ip, "ts": timestamp, "hostreport": get_memory_info()},
            {"chart": 3, "hostserver": local_ip, "ts": timestamp, "hostreport": get_disk_info()},
            {"chart": 4, "hostserver": local_ip, "ts": timestamp, "hostreport": get_kernel_info()},
            {"chart": 5, "hostserver": local_ip, "ts": timestamp, "hostreport": get_net_io_counters()},
            {"chart": 6, "hostserver": local_ip, "ts": timestamp, "hostreport": get_system_uptime()},
            {"chart": 7, "hostserver": local_ip, "ts": timestamp, "hostreport": get_temperature_info()},
            {"chart": 8, "hostserver": local_ip, "ts": timestamp, "hostreport": check_for_updates()},
            {"chart": 9, "hostserver": local_ip, "ts": timestamp, "hostreport": count_users()},
            {"chart": 10, "hostserver": local_ip, "ts": timestamp, "hostreport": list_active_connections()},
        ],
        "hosts": {
            "_id": local_ip,
            "Created": timestamp,
            "Info": hostname.upper(),
            "Type": hostname_short,
        },
    }
    #logger.info(system_data["hostreports"], "hostreports")
    return system_data

def upload_to_mongodb(data, collection_name):
    # Insert data into the specified collection
    collection = db.get_collection(collection_name)

    try:
        if isinstance(data, list):
            collection.insert_many(data)
        else:
            collection.insert_one(data)
    except BulkWriteError as bwe:
        for error in bwe.details['writeErrors']:
            if error['code'] == 11000:  # Duplicate key error code
                logger.warning(f"Duplicate key error in collection '{collection_name}': {error['errmsg']}")
                # Try to update the existing document
                try:
                    _id = None
                    if isinstance(data, dict):
                        _id = data.get('_id')
                        if _id:
                            collection.update_one({'_id': _id}, {'$set': data}, upsert=True)
                            logger.info(f"Updated document with _id: {_id}")
                        else:
                            logger.warning("Document does not have _id field, skipping update.")
                except Exception as e:
                    logger.warning(f"Failed to update document with _id: {_id}, error: {str(e)}")
            else:
                raise  # Re-raise the exception if it's not a duplicate key error
    except DuplicateKeyError as dke:
        logger.warning(f"Duplicate key error in collection '{collection_name}': {str(dke)}")


def main():
    start_time = time.time()
    system_data = get_system_info()
    hostcharts / hosts when needed to create on mongodb
    upload_to_mongodb(system_data["hostcharts"], "hostcharts")
    upload_to_mongodb(system_data["hosts"], "hosts")
    upload_to_mongodb(system_data["hostreports"], "hostreports")

    end_time = time.time()
    execution_time = end_time - start_time

    logger.info("System information and charts successfully stored in MongoDB.")
    logger.info(f"Execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()
