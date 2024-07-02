# System Information Tool

This Python tool collects and stores system information in a MongoDB database. The information includes CPU, memory, disk, network, system uptime, temperature, and user details. It also checks for available updates.

## Features

- Collects CPU, memory, disk, network, and uptime information.
- Retrieves system temperature for CPU and specific disks.
- Counts total and active users.
- Lists active network connections.
- Checks for operating system updates.
- Stores collected information in a MongoDB database.

## Requirements

- Python 3.7+
- MongoDB
- Required Python packages (listed in `requirements.txt`)
- `smartmontools` for disk temperature readings

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/P1ro/syspynfo.git
   cd syspynfo
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the required Python packages:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install `smartmontools`:**

   - **Debian/Ubuntu:**

     ```bash
     sudo apt-get install smartmontools
     ```

   - **Arch Linux:**

     ```bash
     sudo pacman -S smartmontools
     ```

   - **Gentoo:**

     ```bash
     sudo emerge sys-apps/smartmontools
     ```

   - **CentOS:**

     ```bash
     sudo yum install smartmontools
     ```

5. **Configure MongoDB connection:**

   Create a `config.yaml` file with the following structure:

   ```yaml
   mongo_uri: "your_mongo_db_uri"
   database_name: "your_database_name"
   ```

## Usage

1. **Run the tool:**

   ```bash
   ./.venv/bin/python syspynfo.py
   ```

2. **Output:**

   The tool will log the collected information and execution time. The information will be stored in the specified MongoDB database under the collections `hostcharts`, `hostreports`, and `hosts`.

## Functions

- `convert_to_kilobytes(value)`: Converts bytes to kilobytes.
- `get_local_ip(interface_name)`: Retrieves the local IP address for the given network interface.
- `get_hostname()`: Returns the system hostname.
- `get_kernel_info()`: Collects kernel information.
- `get_operating_system_info()`: Retrieves operating system details.
- `check_for_updates()`: Checks for available OS updates.
- `get_cpu_info()`: Collects CPU information.
- `get_memory_info()`: Retrieves memory details.
- `get_disk_info()`: Collects disk usage information.
- `get_net_io_counters()`: Retrieves network I/O counters.
- `get_system_uptime()`: Calculates system uptime.
- `get_temperature_info()`: Retrieves temperature data for CPU and specified disks.
- `count_users()`: Counts total and active users.
- `list_active_connections()`: Lists active network connections.
- `get_system_info()`: Aggregates all system information.
- `upload_to_mongodb(data, collection_name)`: Uploads collected data to MongoDB.

## Logging

The tool uses Python's logging module to log information. The log level is set to `INFO`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Additional Scripts

### disktemp.sh

This script retrieves the temperature of a specified disk using `smartctl` from `smartmontools`. You can find the script [here](https://github.com/P1ro/syspynfo/blob/main/disktemp.sh).
