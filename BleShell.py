from cmd import Cmd
import pygatt
import time
import argparse
import os
import logging

PYGATT_ENABLE_LOGGING = False

class BleShell(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.ScanTimeoutSeconds = 10.0
        self.ConnectTimeoutSeconds = 10.0
        
        if(PYGATT_ENABLE_LOGGING == True):
            logging.basicConfig()
            logging.getLogger('pygatt').setLevel(logging.DEBUG)
        
        #Initialize and start PyGATT Adapter
        self.BleAdapter = pygatt.GATTToolBackend(search_window_size=2048)
        self.BleAdapter.start()
        
        self.BleDevice = None
        
    def do_scan(self,args):
        '''
        scan: starts BLE scanning
        Params: Scan (optional) timeout in seconds
        
        scan
        
        scan -t 30
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument("-t","--ScanTimeout", help="Scan timeout in seconds")
                
        try:
            CommandArgs,_ = parser.parse_known_args(args.split())
        except:
            #avoid application to exit when parsing fails
            pass
        else:
    
            #Timeout means the number of seconds the application is blocked scanning
            if(CommandArgs.ScanTimeout is not None):
                self.ScanTimeoutSeconds = float(CommandArgs.ScanTimeout)
            
            print("Scanning for {} seconds\n\r".format(self.ScanTimeoutSeconds))
            
            try:
                ScannedDevices = self.BleAdapter.scan(timeout=self.ScanTimeoutSeconds)
                
                if(ScannedDevices is not None):
                    
                    print("Found {} devices".format(len(ScannedDevices)))
                    
                    if(len(ScannedDevices) > 0):
                        #scan returns a dictionary for each device containing the name and address
                        for Device in ScannedDevices:
                            DeviceAddress = Device['address']
                            DeviceName = Device['name']
                            
                            print("Found device {} with BDADDR {}".format(DeviceName,DeviceAddress))
                        
                        print("\n\r")

                else:
                    print("No devices found")
            except pygatt.exceptions.BLEError:
                print("Error while scanning")
                pass
            
    def do_connect(self,args):
        '''
        connect: tries to connect to the specified BDADDR
        Params: BDADDR to connect to
        Params: ConnectionTimeout (optional). Number of seconds we'll try to connect

        connect 11:22:33:44:55 -t 5
        
        connect 11:22:33:44:55
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument("PeripheralBdAddr", help="tries to connect to the specified BDADDR")
        parser.add_argument("-t","--ConnectTimeout", help="Connection timeout in seconds")

        '''
        During tesing, I've found that a a large timeout may confuse PyGATT and even if the device connects
        it will return a non-connected error. Default 10 seconds worked in must cases
        '''

        try:
            CommandArgs,_ = parser.parse_known_args(args.split())
        except:
            #avoid application to exit when parsing fails
            pass
        else:
            if(CommandArgs.ConnectTimeout is not None):
                self.ConnectTimeoutSeconds = float(CommandArgs.ConnectTimeout)
            
            try:
                print("Trying to connect to {}".format(CommandArgs.PeripheralBdAddr))
        
                #PyGATT API requires the BDADDR as a string. Optinally, the connect timeout
                #a more advanced implementation can set the address type (public/random)
                self.BleDevice = self.BleAdapter.connect(CommandArgs.PeripheralBdAddr,timeout = self.ConnectTimeoutSeconds)
                
                #Register callback to be executed if the device gets disconnected
                self.BleDevice.register_disconnect_callback(self.DisconnectCallback)
                print("Device Connected")
                
            except:
                print("Couldn't connect to device {}".format(CommandArgs.PeripheralBdAddr))
                pass
                
    def do_disconnect(self,args):
        '''
        disconnect: Disconnects current BLE device
        '''    
                
        if(self.BleDevice is not None):
            self.BleDevice.remove_disconnect_callback(self.DisconnectCallback)
            self.BleDevice.disconnect()
            print("Disconnecting from device")
        
        self.BleDevice = None
        
    def do_get_char(self,args):
        '''
        get_char: Reads the BLE Devices characteristics and prints the corresponding UUIDs
        Params: None
        '''
        if(self.BleDevice is not None):
        
            try:
                #discover characteristic gets you the UUID
                #returns a dictionary where each key is a characteristic UUID
                CharacteristicsFound = self.BleDevice.discover_characteristics()
                print("Found {} characteristics".format(len(CharacteristicsFound)))
                
                #print each UUID found with its corresponding handle
                for AttributeUuid in CharacteristicsFound.keys():
                    AttHandle = self.BleDevice.get_handle(AttributeUuid)
                    
                    print("Characteristic UUID: {} with handle {}".format(AttributeUuid,hex(AttHandle)))
                    
                '''
                up to this point, you must know the server GATT database as there's no extra details
                because discover_characteristics only shows the characteristics UUIDs but not the primary
                services or the underlying attributes of each characteristic as CCCDs
                
                Usually the handles are continuous numbers, so, you'll see some skipped, meaning there's 
                more attributes within that characteristic. For example, a heartrate monitor shows UUID 00002a37
                with handle 0x10, the next characteristic shows handle 0x13, meaning handles 0x11 and 0x12 
                are part attributes of characteristic 00002a37.
                
                Today, there's no easy way out here but to know how GATT servers work and the specific
                server used to continue
                '''
                
                #haven't found a way to make primary services discovery with PyGATT (limitation?)
                                
            except:
                print("Error while reading characteristics")
                pass
        
        else:
            print("Must have a BLE device connected")
            
    def do_notification(self,args):
        '''
        notification: Enables or disables notifications of a given characteristic. When data is received, will be
                      printed
        Params: Characteristic UUID
        Params: on/off depending on the action to be performed
        
        notification 00000000-0000-0000-0000-000000000000 on
        
        Notification received from handle 0x00
        Data: 0x1e4effff06002000
        Notification received from handle 0x00
        Data: 0x1ec8ffff0000a000
        Notification received from handle 0x00
        Data: 0x1e7affff02005000
        
        notification 00000000-0000-0000-0000-000000000000 off
        '''
    
        parser = argparse.ArgumentParser()
        parser.add_argument("CharUuid", help="Characteristic UUID to enable|disable notification to")
        parser.add_argument("Status", help="on|off")
        
        try:
            CommandArgs,_ = parser.parse_known_args(args.split())
        except:
            #avoid application to exit when parsing fails
            pass
        else:
        
            if(CommandArgs.Status == "on"):
                try:
                    #Subscribe must register a callback which is executed each time data is received
                    #The API looks for the characteristic CCCD and enables it
                    self.BleDevice.subscribe(CommandArgs.CharUuid, callback = self.HandleNotification, indication = False)
                    print("Notification enabled")
                except:
                    print("Error while enabling notifications to UUID {}".format(CommandArgs.CharUuid))
                    pass
            elif(CommandArgs.Status == "off"):
                try:
                    #Unsubscribe disables the CCCD
                    self.BleDevice.unsubscribe(CommandArgs.CharUuid)
                    print("Notification disabled")
                except:
                    print("Error while disabling notifications to UUID {}".format(CommandArgs.CharUuid))
                    pass

    def do_indication(self,args):
        '''
        indication: Enables or disables indications of a given characteristic (if supported)
        Params: Characteristic UUID
        Params: on/off depending on the action to be performed
        
        indication 00000000-0000-0000-0000-000000000000 on
        
        indication received from handle 0x00
        Data: 0x1e4effff06002000
        indication received from handle 0x00
        Data: 0x1ec8ffff0000a000
        indication received from handle 0x00
        Data: 0x1e7affff02005000
        
        indication 00000000-0000-0000-0000-000000000000 off
        
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument("CharUuid", help="Characteristic UUID to enable|disable indications to")
        parser.add_argument("Status", help="on|off")
        
        try:
            CommandArgs,_ = parser.parse_known_args(args.split())
        except:
            #avoid application to exit when parsing fails
            pass
        else:
        
            if(CommandArgs.Status == "on"):
                try:
                    #Subscribe must register a callback which is executed each time data is received
                    #The API looks for the characteristic CCCD and enables it
                    self.BleDevice.subscribe(CommandArgs.CharUuid, callback = self.HandleIndication, indication = True)
                    print("Indication enabled")
                except:
                    print("Error while enabling indications to UUID {}".format(CommandArgs.CharUuid))
                    pass
            elif(CommandArgs.Status == "off"):
                try:
                    self.BleDevice.unsubscribe(CommandArgs.CharUuid)
                    print("Indication disabled")
                except:
                    print("Error while disabling indications to UUID {}".format(CommandArgs.CharUuid))
                    pass
    
    def do_get_handle(self,args):
        '''
        get_handle: Returns the handle corresponding to the characteristic UUID sent as argument
        Params: Characteristic UUID
        
        get_handle 00000000-0000-0000-0000-000000000000
        Handle 0x00

        '''
        parser = argparse.ArgumentParser()
        parser.add_argument("CharUuid", help="Characteristic UUID to get handle")    
        try:
            CommandArgs,_ = parser.parse_known_args(args.split())
        except:
            #avoid application to exit when parsing fails
            pass
        else:
            
            try:
                CharHandle = self.BleDevice.get_handle(CommandArgs.CharUuid)
            except:
                print("Error while getting handle from UUID {}".format(CommandArgs.CharUuid))
                pass
            else:
                print("Handle {}".format(hex(CharHandle)))
                print("Handle {}".format(CharHandle))
                
    def do_char_read_uuid(self,args):
        '''
        char_read_uuid: Reads a characteristic by using the UUID
        Params: Characteristic UUID
        
        char_read_uuid 00000000-0000-0000-0000-000000000000
        Read data: 12DEA5
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument("CharUuid", help="Characteristic UUID to read")
        
        try:
            CommandArgs,_ = parser.parse_known_args(args.split())
        except:
            #avoid application to exit when parsing fails
            pass
        else:
            
            try:
                ReadData = self.BleDevice.char_read(CommandArgs.CharUuid)
            except:
                print("Error while reading characteristic {}".format(CommandArgs.CharUuid))
                pass
            else:
                print("Read data: " + str(ReadData.hex()))

    def do_char_read_handle(self,args):
        '''
        char_read_handle: Reads a characteristic by using the handle
        Params: Characteristic handle
        
        char_read_handle 0x0000
        Read data: 12DEA5
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument("CharHandle", help="Characteristic handle to read (hex)")
        
        try:
            CommandArgs,_ = parser.parse_known_args(args.split())
        except:
            #avoid application to exit when parsing fails
            pass
        else:           
            try:
                #Get the handle value to be requested
                HandleValue = CommandArgs.CharHandle.split("0x",1)
            
                ReadData = self.BleDevice.char_read_handle(HandleValue[1])
            except:
                print("Error while reading characteristic {}".format(CommandArgs.CharHandle))
                pass
            else:
                print("Read data: " + str(ReadData.hex()))             
                
    def do_char_write_req(self,args):
        '''
        char_write_req: Writes data to the given characteristic using write request
        Params: Characteristic UUID
        Params: Data to be written in hex
        
        char_write_req 00000000-0000-0000-0000-000000000000 12DEA5345F
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument("CharUuid", help="Characteristic Uuid to write")
        parser.add_argument("CharData", help="Characteristic data (hex)")
        
        try:
            CommandArgs,_ = parser.parse_known_args(args.split())
        except:
            #avoid application to exit when parsing fails
            pass
        else:
            try:                        
                DataToSend = bytearray.fromhex(CommandArgs.CharData)
                
                self.BleDevice.char_write(CommandArgs.CharUuid, DataToSend, wait_for_response=True)
            except:
                print("Error while writting characteristic {}".format(CommandArgs.CharHandle))
                pass
            else:
                print("Data written")
                
    def do_char_write_cmd(self,args):
        '''
        char_write_cmd: Writes data to the given characteristic using write command
        Params: Characteristic UUID
        Params: Data to be written in hex
        
        char_write_cmd 00000000-0000-0000-0000-000000000000 12DEA5345F
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument("CharUuid", help="Characteristic Uuid to write")
        parser.add_argument("CharData", help="Characteristic data (hex)")
        
        try:
            CommandArgs,_ = parser.parse_known_args(args.split())
        except:
            #avoid application to exit when parsing fails
            pass
        else:
            try:           
                DataToSend = bytearray.fromhex(CommandArgs.CharData)
                
                self.BleDevice.char_write_handle(CommandArgs.CharUuid, DataToSend, wait_for_response=False)
            
            except:
                print("Error while writting characteristic {}".format(CommandArgs.CharHandle))
                pass
            else:
                print("Data written")
                
    def do_exit(self,args):
        '''
        exit: Terminates the application
        '''        
        if(self.BleDevice is not None):
            self.BleDevice.disconnect()
        
        self.BleAdapter.stop()
        
        os._exit(0)
    
    def do_EOF(self, line):
        
        if(self.BleDevice is not None):
            self.BleDevice.disconnect()
        
        self.BleAdapter.stop()
        
        return True
    
    def emptyline(self):
         pass
        
    def HandleNotification(self,Handle,Value):
        print("Notification received from handle {}".format(hex(Handle)))
        print("Data: 0x{}".format(Value.hex()))
                
    def HandleIndication(self,Handle,Value):
        print("Indication received from handle {}".format(hex(Handle)))
        print("Data: 0x{}".format(Value.hex()))
    
    def DisconnectCallback(self,Event):
        try:
            print("Device disconnected")
            self.BleDevice.disconnect()
            
        except NotConnectedError:
            pass
            
        self.BleDevice = None

if __name__ == '__main__':                
            
    Shell = BleShell()
    
    Shell.prompt = 'BLEShell>'
    
    Shell.cmdloop("Starting BLE shell")
        