import json
import time

import config
import paho.mqtt.client as mqtt
import serial
import serial.tools.list_ports


class DecawaveModule:
	
	def __init__(self, debug: bool = False):
		self.debug = debug
		self.port = None
		self.stop_reading = False
		self.px = 0.0	# X position
		self.py = 0.0	# Y position
		self.pz = 0.0	# Z position
		self.qf = 0		# quality factor
		
		self.client = mqtt.Client("decawave")


	def _find_portname(self) -> str:
		"""Find and return the name of the device's serial port."""
		portname = None
		ports = serial.tools.list_ports.comports()
		for port in ports:
			# SEGGER Embedded Studio is used for the software
			# development of the Decawave UWB modules.
			if port.manufacturer == "SEGGER":
				portname = f"/dev/{port.name}"
				break
		if portname is None:
			raise RuntimeError("UWB: No serial port found")
		print(f"UWB: Device found with port={portname}") 
		return portname


	def _read(self, send_data: bool = False, wait_network: bool = False):
		"""
		Read the output of the shell command.
		
		:param bool send_data: Send the output to the MQTT server.
		:param bool wait_network: Wait the module to rejoin to UWB network.

		"""
		time.sleep(0.1)
		while True:
			if self.stop_reading is True:
				print("UWB: Stopping...")
				break
			try:
				data = self.port.readline(256)
				if len(data) == 0:
					# No data because the anchors are out of range
					# -> wait for the tag to rejoin the UWB network.
					if wait_network:
						time.sleep(10)
						continue
					# No more output data -> exit while loop.
					break
				output = data.decode().replace("\r\n", "")
				
				if self.debug:
					print(output)
				
				if send_data is False:
					continue
				# Expected output of the 'les' shell command:
				# '<range_measurements> est[<x>,<y>,<z>,<qf>]'
				# Check if the output contains the estimated position.
				pos_estimate = 0 if output.find("est") == -1 else 1

				if pos_estimate == 1:
					p = output.split("est[")[1].split("]")[0].split(",")
					try:
						self.px = float(p[0])
						self.py = float(p[1])
						self.pz = float(p[2])
						self.qf = int(p[3])
					except ValueError:
						pass
					except IndexError:
						pass

				uwbdata = {
					"px": self.px,
					"py": self.py,
					"pz": self.pz,
					"qf": self.qf,
					"uwbFixOk": pos_estimate
				}
				payload = json.dumps(uwbdata)
				self.client.publish(config.MQTT_TOPIC_UWB, payload)
				
			except KeyboardInterrupt:
				break


	def read(self):
		"""Read range measurements and estimated position."""

		portname = self._find_portname()
		self.client.connect(config.MQTT_HOST, config.MQTT_PORT)

		# Define a timeout since the readline() could block forever if
		# no newline character is received.
		self.port = serial.Serial(portname, baudrate=115200, timeout=1)

		# Go to the shell mode by writing ENTER twice.
		self.port.write(b'\r\r')
		self._read()

		# Get range measurements and estimated position if the tag.
		# Writing 'les' shell command multiple times will turn on/off
		# the functionality. 
		print("UWB: Reading...")
		self.port.write(b'les\n')
		self._read(send_data=True, wait_network=True)
		self.stop_reading = False
		self.port.write(b'les\n')
		self._read()

		# Exit the shell mode and go to the generic mode.
		self.port.write(b'quit\n')
		self._read()

		self.port.close()
		self.client.disconnect()
		print("UWB: Reading stopped")
