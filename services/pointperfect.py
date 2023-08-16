import os
import sys
from typing import Callable

import paho.mqtt.client as mqtt


class PointPerfect():
    """
    u-blox PointPerfect client class.

    :param str host: Hostname of PointPerfect service.
    :param int port: Port number of the PointPerfect service.
    :param str clientid: Client ID of the PointPerfect service.
    :param str topic: Topic from which to read GNSS correction data.
    :param str certdir: Path to certificate directory.

    """

    def __init__(
            self,
            host: str,
            port: int,
            clientid: str,
            topic: str,
            certdir: str
        ) -> None:
        self.host = host
        self.port = port
        self.clientid = clientid
        self.topic = topic

        self.certfile = os.path.join(certdir, f"device-{clientid}-pp-cert.crt")
        self.keyfile = os.path.join(certdir, f"device-{clientid}-pp-key.pem")
        self.stop_reading = False


    def on_connect(self, client: mqtt.Client, userdata, flags, rc: int):
        """
        Called when the broker responds to the connection request.

        :param Client client:
        :param Any userdata:
        :param dict flags:
        :param int rc: Return code.

        """
        if rc == 0:
            print("POINTPERFECT: Connected")
            print("POINTPERFECT: Reading...")
            client.subscribe(self.topic)
            #client.subscribe("/pp/ubx/mga")
            #client.subscribe("/pp/ubx/0236/ip")
        else:
            print(f"POINTPERFECT: connection error, rc={rc}")
            sys.exit(1)


    def on_disconnect(self, client, userdata, rc):
        """Called when the client disconnects from the broker."""
        if rc == 0:
            print("POINTPERFECT: Disconnected")
        else:
            print(f"POINTPERFECT: Unexpected disconnection: rc={rc}")


    def on_message(self, client, userdata, message: mqtt.MQTTMessage):
        """
        Called when a message has been received on a topic that the
        client subscribes to.

        :param Client client:
        :param Any userdata:
        :param MQTTMessage message:

        """
        # Write the received GNSS correction data to the GNSS rover.
        userdata(message.payload)


    def read(self, rover_writer: Callable):
        """
        Read GNSS correction data from u-blox PointPerfect service.
        
        :param Callable rover_writer: Function to write data to the GNSS rover.

        """
        # MQTT client object.
        client = mqtt.Client(client_id=self.clientid)
        # Add the callback functions to the user data.
        client.user_data_set(rover_writer)
        # Set the credentials of the PointPerfect service.
        client.tls_set(certfile=self.certfile, keyfile=self.keyfile)
        # Set callback functions.
        client.on_connect = self.on_connect
        client.on_disconnect = self.on_disconnect
        client.on_message = self.on_message
        # Connect to the PointPerfect service.
        client.connect(host=self.host, port=self.port)

        # Read GNSS correction data until the stopflag is received.
        while True:
            client.loop()
            if self.stop_reading:
                break
        client.loop_stop()
        client.disconnect()
        print("POINTPERFECT: Reading stopped")
