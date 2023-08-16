import ctypes
import os
import pathlib
from threading import Thread
import time

import config
from sensors.gps import UbloxGNSSRover
from sensors.uwb import DecawaveModule
from services.ntrip import NTRIPClient
from services.pointperfect import PointPerfect


def main():
	gpssensor = UbloxGNSSRover()
	gpssensor.open_port()
	
	uwbsensor = DecawaveModule()

	# Use Python bindings to call a separate C++ application to read
	# IMU sensor data since the Xsens' Python XDA code is incompatible
	# with the ARM architecture.
	apppath = pathlib.Path().absolute()
	libname = os.path.join(apppath, "sensors/imu.so")
	imusensor = ctypes.CDLL(libname)
	
	# GNSS correction data service.
	service = None
	if config.GNSS_CORRECTION_DATA_SERVICE == config.NTRIP_SERVICE_NAME:
		service = NTRIPClient(
			host=config.NTRIP_HOST,
			port=config.NTRIP_PORT,
			auth=config.NTRIP_AUTH,
			mountpt=config.NTRIP_MOUNTPT
		)
	elif config.GNSS_CORRECTION_DATA_SERVICE == config.PP_SERVICE_NAME:
		service = PointPerfect(
			host=config.PP_HOST,
			port=config.PP_PORT,
			clientid=config.PP_CLIENT_ID,
			topic=config.PP_TOPIC,
			certdir=os.path.join(apppath, config.PP_CERT_DIR)
		)
	else:
		raise RuntimeError("Invalid GNSS correction data service")
	
	# Threads for reading sensor data and GNSS correction data.
	thread1 = Thread(target=gpssensor.read)
	thread2 = Thread(target=imusensor.main)
	thread3 = Thread(target=uwbsensor.read)
	thread4 = Thread(target=service.read, args=(gpssensor.write,))
	
	thread1.start()
	thread2.start()
	thread3.start()
	thread4.start()
	
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		gpssensor.stop_reading = True
		uwbsensor.stop_reading = True
		service.stop_reading = True
	
	thread1.join()
	thread2.join()
	thread3.join()
	thread4.join()
	
	gpssensor.close_port()


if __name__ == "__main__":
	main()
