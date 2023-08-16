import socket
from typing import Callable


class NTRIPClient:
    """
    NTRIP client for reading GNSS correction data from the NTRIP caster.

    :param str host: Hostname of the NTRIP caster.
    :param int port: Port number of the NTRIP caster.
    :param str auth: Username.
    :param str mountpt: Mount point from which the data is read from.

    """
    def __init__(self, host: str, port: int, auth: str, mountpt: str) -> None:
        self.host = host
        self.port = port
        self.auth = auth
        self.mountpt = mountpt
        
        self.stop_reading = False
    

    def _mountpt_request(self) -> str:
        """
        Create a request to receive data from a mount point.

        The request string is valid for the NTRIP revision 1.

        :return: Mount point request.
        :rtype: str

        """
        request = f"GET /{self.mountpt} HTTP/1.0\r\n"
        request += f"User-Agent: NTRIP RaspberryPi/3\r\n"
        request += f"Authorization: {self.auth}\r\n"
        return request
    
    
    def loop_stop(self):
        self.stop_reading = True
    

    def read(self, rover_writer: Callable = None):
        """
        Read GNSS correction data from the mount point in NTRIP caster.

        :param Callable rover_writer: Function that writes data to GNSS rover.

        """
        print("NTRIP: Connecting...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        error_number = sock.connect_ex((self.host, self.port))
        if not error_number == 0:
            print(f"NTRIP: Connection error, {error_number}")
            return
        
        request = self._mountpt_request()
        sock.sendall(request.encode())
        print("NTRIP: Reading...")
        while True:
            if self.stop_reading is True:
                print("NTRIP: Stopping...")
                break
            try:
                data = sock.recv(4096)
                if len(data) == 0:
                    break
                if rover_writer is not None:
                    rover_writer(data)
            except KeyboardInterrupt:
                break
        
        sock.close()
        print("NTRIP: Reading stopped")
