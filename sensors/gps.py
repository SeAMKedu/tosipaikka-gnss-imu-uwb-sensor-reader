import json

import paho.mqtt.client as mqtt
import pyubx2
import serial
import serial.tools.list_ports

import config


class UbloxGNSSRover:
    """
    u-blox C099-F9P GNSS receiver class.
    """
    def __init__(self) -> None:

        self.port = None
        self.stop_reading = False
    

    def _find_portname(self) -> str:
        """
        Find the name of the serial port of the GNSS receiver.

        :raises: RuntimeError if the serial port is not found.
        :return: Port name.
        :rtype: str

        """
        portname = None
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.description == "u-blox GNSS receiver":
                portname = f"/dev/{port.name}"
                break
        if portname is None:
            raise RuntimeError("GPS: No serial port found")
        print(f"GPS: Device found with port={portname}")
        return portname
    

    def _parse_ubxmessage(self, message: pyubx2.UBXMessage) -> dict:
        """
        Convert the UBX message into a dictionary.

        :param UBXMessage message: UBX message to be parsed.
        :returns: Parsed UBX message.
        :rtype: dict

        """
        msg = str(message)
        # Convert <UBX(..., param1=value1, ..., paramN=valueN)>
        # to [[...], ['param1','value1'], ..., ['paramN','valueN']].
        items = [m.lstrip().replace(")>", "").split("=") for m in msg.split(",")]
        # Convert the list to {'param1': 'value1', ..., 'paramN': 'valueN'}.
        data = {item[0]: item[1] for item in items[1:]}
        # Data type of the values is now a string. Set the correct data type.
        for key, value in list(data.items())[1:]:
            data[key] = float(value) if value.find(".") != -1 else int(value)
        return data


    def open_port(self):
        """Open the serial port."""

        portname = self._find_portname()
        self.port = serial.Serial(portname, baudrate=115200, timeout=1)


    def close_port(self):
        """Close the serial port."""

        if self.port is not None:
            self.port.close()


    def read(self):
        """Read data from the GNSS receiver over the serial port."""
        
        if self.port is None:
            print("GPS: Error, the serial port is not open")
            return
        
        client = mqtt.Client("ublox")
        client.connect(config.MQTT_HOST, config.MQTT_PORT)

        # Read only the UBX messages by setting protfilter=2.
        reader = pyubx2.UBXReader(datastream=self.port, protfilter=2)
        # UBX-NAV-PVT message contains position, velocity, and time
        # solution including the number of the used satellites.
        message = pyubx2.UBXMessage("NAV", "NAV-PVT", pyubx2.POLL)

        print("GPS: Reading...")
        while True:
            if self.stop_reading is True:
                print("\nGPS: Stopping...")
                break
            # Write UBX message without a payload. The device will
            # then return the same message with the payload populated.
            self.port.write(message.serialize())

            try:
                (rawdata, ubxmessage) = reader.read()
                
                if not ubxmessage:
                    continue

                if ubxmessage.identity == "NAV-PVT":
                    data = self._parse_ubxmessage(ubxmessage)
                    payload = json.dumps(data)
                    client.publish(config.MQTT_TOPIC_GPS, payload)
            
            except pyubx2.UBXStreamError as error:
                print(f"GPS: {error}")
            except KeyboardInterrupt:
                break

        client.disconnect()
        print("GPS: Reading stopped")


    def write(self, data: bytes):
        """
        Write data to the GNSS receiver over the serial port.

        :param bytes data: Data to be written.

        """
        if self.port is not None:
            self.port.write(data)

