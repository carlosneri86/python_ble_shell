# PyGATT BLE Shell

This shell is intended to help the usage, debug and control of BLE devices over Python using [PyGATT](https://github.com/peplin/pygatt "PyGATT"). This means this application works as a central at GAP level and as a client at GATT level.

This implementation assumes the user has knowledge of BLE concepts, sucha as, how GATT data bases are generated and used (Services, characteristics, UUIDs, handles, etc).

## Environment
Developed and tested under the following conditions:
- Ubuntu 18.04.4 via a Virtual Machine
- USB Bluetooth v4.0 dongle
- Python v3.6.9
- BlueZ v5.48
- PyGATT v4.0.5
    - GATTTool backend   

## Setup
Install [PyGATT](https://github.com/peplin/pygatt "PyGATT") using pip or any of the other methods mentioned on the project documentation.

```console
$ pip install pygatt
```
As per PyGATT documentation, BlueZ 5.18 or greater is required. Verify your version as follows:

```console
$ dpkg --status bluez | grep '^Version:'
```

The script assumes there's a working HCI interface. To verify, use BlueZ HCI Config:

```console
$ hciconfig
hci0:	Type: Primary  Bus: USB
	BD Address: 00:1A:7D:DA:71:11  ACL MTU: 310:10  SCO MTU: 64:8
	UP RUNNING 
	RX bytes:98087 acl:265 sco:0 events:4587 errors:0
	TX bytes:49560 acl:224 sco:0 commands:2264 errors:0
```

Also, assume the interface is BLE capable. Rewiew the HCI interface BLE capabilities:

```console
$ sudo hciconfig hci0 lestates
Supported link layer states:
	YES Non-connectable Advertising State
	YES Scannable Advertising State
	YES Connectable Advertising State
	YES Directed Advertising State
	YES Passive Scanning State
	YES Active Scanning State
	YES Initiating State/Connection State in Master Role
	YES Connection State in the Slave Role
	YES Non-connectable Advertising State and Passive Scanning State combination
	YES Scannable Advertising State and Passive Scanning State combination
	YES Connectable Advertising State and Passive Scanning State combination
	YES Directed Advertising State and Passive Scanning State combination
	YES Non-connectable Advertising State and Active Scanning State combination
	YES Scannable Advertising State and Active Scanning State combination
	YES Connectable Advertising State and Active Scanning State combination
	YES Directed Advertising State and Active Scanning State combination
	YES Non-connectable Advertising State and Initiating State combination
	YES Scannable Advertising State and Initiating State combination
	YES Non-connectable Advertising State and Master Role combination
	YES Scannable Advertising State and Master Role combination
	YES Non-connectable Advertising State and Slave Role combination
	YES Scannable Advertising State and Slave Role combination
	YES Passive Scanning State and Initiating State combination
	YES Active Scanning State and Initiating State combination
	YES Passive Scanning State and Master Role combination
	YES Active Scanning State and Master Role combination
	YES Passive Scanning State and Slave Role combination
	YES Active Scanning State and Slave Role combination
	YES Initiating State and Master Role combination/Master Role and Master Role combination
```

An output similar to this means the interface supports BLE.

## Usage
Execute the script as follows, sudo maybe required as GATTTool and HCITool needs them to access the interfaces:

```console
$ sudo python BleShell.py
Starting BLE shell
BLEShell>
```

List of supported commands:

|BLE Shell Commands|
|:----------------:|
|scan|
|connect|
|disconnect|
|get_char|
|get_handle|
|notification|
|indication|
|char_read_handle|
|char_read_uuid|
|char_write_cmd|
|char_write_req|
|exit|
|help|

To get more details on each command, type "help <command>"

```console
BLEShell>help char_write_req

        char_write_req: Writes data to the given characteristic using write request
        Params: Characteristic UUID
        Params: Data to be written in hex
        
        char_write_req 00000000-0000-0000-0000-000000000000 12DEA5345F
```
Following example shows interaction with a sample device that simulates a Heart Rate Sensor. First a **scan** is used to look for the device. Once found, execute **connect** with the devices address. Now that the device is connected, use **get_char** to list the characteristics. It is known that UUID 0x2A37 is the [heart rate measurement](https://www.bluetooth.com/specifications/gatt/characteristics/) and uses notifications to report measurements. With **notifications** enabled, the device starts sending data. Now turn off notifications and **disconnect** the device:
```console
Starting BLE shell
BLEShell>scan
Scanning for 10.0 seconds

Found 1 devices
Found device NXP_HRS with BDADDR 00:60:37:38:81:47

BLEShell>connect 00:60:37:38:81:47
Trying to connect to 00:60:37:38:81:47
Device Connected
BLEShell>get_char
Found 16 characteristics
Characteristic UUID: 00002a05-0000-1000-8000-00805f9b34fb with handle 0x3
Characteristic UUID: 00002a00-0000-1000-8000-00805f9b34fb with handle 0x8
Characteristic UUID: 00002a01-0000-1000-8000-00805f9b34fb with handle 0xa
Characteristic UUID: 00002a04-0000-1000-8000-00805f9b34fb with handle 0xc
Characteristic UUID: 00002a37-0000-1000-8000-00805f9b34fb with handle 0x10
Characteristic UUID: 00002a38-0000-1000-8000-00805f9b34fb with handle 0x13
Characteristic UUID: 00002a39-0000-1000-8000-00805f9b34fb with handle 0x15
Characteristic UUID: 00002a19-0000-1000-8000-00805f9b34fb with handle 0x19
Characteristic UUID: 00002a29-0000-1000-8000-00805f9b34fb with handle 0x1f
Characteristic UUID: 00002a24-0000-1000-8000-00805f9b34fb with handle 0x21
Characteristic UUID: 00002a25-0000-1000-8000-00805f9b34fb with handle 0x23
Characteristic UUID: 00002a27-0000-1000-8000-00805f9b34fb with handle 0x25
Characteristic UUID: 00002a26-0000-1000-8000-00805f9b34fb with handle 0x27
Characteristic UUID: 00002a28-0000-1000-8000-00805f9b34fb with handle 0x29
Characteristic UUID: 00002a23-0000-1000-8000-00805f9b34fb with handle 0x2b
Characteristic UUID: 00002a2a-0000-1000-8000-00805f9b34fb with handle 0x2d
BLEShell>notification 00002a37-0000-1000-8000-00805f9b34fb on
Notification enabled
BLEShell>
Notification received from handle 0x10
Data: 0x1eae540b06008000
Notification received from handle 0x10
Data: 0x1e83b80b0b005000
Notification received from handle 0x10
Data: 0x1e991c0c01007000
Notification received from handle 0x10
Data: 0x1ebe800c06009000
Notification received from handle 0x10
Data: 0x1e96e40c0e006000
Notification received from handle 0x10
Data: 0x1e7f480d07005000
Notification received from handle 0x10
Data: 0x1eb8ac0d00009000
Notification received from handle 0x10
Data: 0x1e83100e0b005000
BLEShell>notification 00002a37-0000-1000-8000-00805f9b34fb off
Notification disabled
BLEShell>disconnect
Disconnecting from device
```
## Wishlist
- Use of pairing and bonding
- Use of privacy
- Automatic recognition and parsing of Bluetooth SIG UUIDs
- Handle multiple devices
- Better parsing usage of exceptions