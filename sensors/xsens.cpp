// xsens.cpp
//  Copyright (c) 2003-2021 Xsens Technologies B.V. or subsidiaries worldwide.
//  All rights reserved.
//  
//  Redistribution and use in source and binary forms, with or without modification,
//  are permitted provided that the following conditions are met:
//  
//  1.	Redistributions of source code must retain the above copyright notice,
//  	this list of conditions, and the following disclaimer.
//  
//  2.	Redistributions in binary form must reproduce the above copyright notice,
//  	this list of conditions, and the following disclaimer in the documentation
//  	and/or other materials provided with the distribution.
//  
//  3.	Neither the names of the copyright holders nor the names of their contributors
//  	may be used to endorse or promote products derived from this software without
//  	specific prior written permission.
//  
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
//  EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
//  MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
//  THE COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
//  SPECIAL, EXEMPLARY OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT 
//  OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
//  HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY OR
//  TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.THE LAWS OF THE NETHERLANDS 
//  SHALL BE EXCLUSIVELY APPLICABLE AND ANY DISPUTES SHALL BE FINALLY SETTLED UNDER THE RULES 
//  OF ARBITRATION OF THE INTERNATIONAL CHAMBER OF COMMERCE IN THE HAGUE BY ONE OR MORE 
//  ARBITRATORS APPOINTED IN ACCORDANCE WITH SAID RULES.
/***********************************************************************
 * Use public Xsens device API to read free acceleration, quaternions,
 * and Euler angles from the Xsens MTi-630 motion tracker, and
 * publish the data to the MQTT server.
 * 
 * CallbackHandler class by Xsens Technologies B.V.
 * 
 * Combile application:
 * $ make
 * 
 * Run application:
 * $ sudo ./xsens
 *
 **********************************************************************/
#include <chrono>               // date and time utilities
#include <exception>			// error handling, assert()
#include <iostream>             // cout
#include <string>               // string

#include <xscontroller/xscontrol_def.h>
#include <xscontroller/xsdevice_def.h>
#include <xscontroller/xsscanner.h>
#include <xstypes/xsoutputconfigurationarray.h>
#include <xstypes/xsdatapacket.h>
#include <xstypes/xstime.h>
#include <xscommon/xsens_mutex.h>

#include "mqtt/async_client.h"  // MQTT client

using namespace std;
using namespace std::chrono;

// MQTT Definitions.
const string ADDRESS { "tcp://172.17.128.166:1883" };
const string CLIENT_ID { "xsens" };
const string TOPIC { "sensorfusion/imu" };
const int QOS = 0;
const auto INTERVAL = seconds(60);

Journaller* gJournal = 0;

class CallbackHandler : public XsCallback
{
public:
	CallbackHandler(size_t maxBufferSize = 5)
		: m_maxNumberOfPacketsInBuffer(maxBufferSize)
		, m_numberOfPacketsInBuffer(0)
	{
	}

	virtual ~CallbackHandler() throw()
	{
	}

	bool packetAvailable() const
	{
		xsens::Lock locky(&m_mutex);
		return m_numberOfPacketsInBuffer > 0;
	}

	XsDataPacket getNextPacket()
	{
		assert(packetAvailable());
		xsens::Lock locky(&m_mutex);
		XsDataPacket oldestPacket(m_packetBuffer.front());
		m_packetBuffer.pop_front();
		--m_numberOfPacketsInBuffer;
		return oldestPacket;
	}

protected:
	void onLiveDataAvailable(XsDevice*, const XsDataPacket* packet) override
	{
		xsens::Lock locky(&m_mutex);
		assert(packet != 0);
		while (m_numberOfPacketsInBuffer >= m_maxNumberOfPacketsInBuffer)
			(void)getNextPacket();

		m_packetBuffer.push_back(*packet);
		++m_numberOfPacketsInBuffer;
		assert(m_numberOfPacketsInBuffer <= m_maxNumberOfPacketsInBuffer);
	}
private:
	mutable xsens::Mutex m_mutex;

	size_t m_maxNumberOfPacketsInBuffer;
	size_t m_numberOfPacketsInBuffer;
	list<XsDataPacket> m_packetBuffer;
};


int main() {
	// Create MQTT client object.
	mqtt::async_client client(ADDRESS, CLIENT_ID);
	auto connect_options = mqtt::connect_options_builder()
		.keep_alive_interval(INTERVAL)
		.clean_session(true)
		.automatic_reconnect(true)
		.finalize();
	mqtt::topic topic(client, TOPIC, QOS, true);
	client.connect(connect_options)->wait();

	XsControl* control = XsControl::construct();
	assert(control != 0);

	// Lambda function for error handling.
	auto handleError = [=](string errorString)
	{
		control->destruct();
		cout << errorString << endl;
		return -1;
	};


	// Find an MTi device.
    XsPortInfoArray portInfoArray = XsScanner::scanPorts();
	XsPortInfo mtPort;
	for (auto const &portInfo : portInfoArray)
	{
		if (portInfo.deviceId().isMti() || portInfo.deviceId().isMtig())
		{
			mtPort = portInfo;
			break;
		}
	}
	if (mtPort.empty())
		return handleError("IMU: No MTi device found. Aborting.");
	
	cout << "IMU: Device found with port=" 
		<< mtPort.portName().toStdString() << endl;


	if (!control->openPort(mtPort.portName().toStdString(), mtPort.baudrate()))
		return handleError("IMU: Could not open port. Aborting.");

	// Get a device object.
	XsDevice* device = control->device(mtPort.deviceId());
	assert(device != 0);

	// Create and attach a callback handler to the device.
	CallbackHandler callback;
	device->addCallbackHandler(&callback);

	// Configure the device.
	if (!device->gotoConfig())
		return handleError("IMU: Configuration mode error. Aborting.");
	XsOutputConfigurationArray configArray;
	configArray.push_back(XsOutputConfiguration(XDI_PacketCounter, 0));
	configArray.push_back(XsOutputConfiguration(XDI_SampleTimeFine, 0));
	configArray.push_back(XsOutputConfiguration(XDI_FreeAcceleration, 100));
	configArray.push_back(XsOutputConfiguration(XDI_Quaternion, 100));
	if (!device->setOutputConfiguration(configArray))
		return handleError("IMU: Configration error. Aborting.");

	// Put the device into a measurement mode.
	if (!device->gotoMeasurement())
		return handleError("IMU: Measurement mode error. Aborting.");

	cout << "IMU: Reading..." << endl;
	string data;
	while (true)
	{
		if (callback.packetAvailable())
		{

			XsDataPacket packet = callback.getNextPacket();

			data = "{";

			// Free acceleration data.
			if (packet.containsFreeAcceleration())
			{
				XsVector acceleration = packet.freeAcceleration();
				data = data + "\"ax\":" + to_string(acceleration[0]);
				data = data + ",\"ay\":" + to_string(acceleration[1]);
				data = data + ",\"az\":" + to_string(acceleration[2]);
			}

			// Quaternions and Euler angles.
			if (packet.containsOrientation())
			{
				XsQuaternion quaternion = packet.orientationQuaternion();

				data = data + ",\"q0\":" + to_string(quaternion.w());
				data = data + ",\"q1\":" + to_string(quaternion.x());
				data = data + ",\"q2\":" + to_string(quaternion.y());
				data = data + ",\"q3\":" + to_string(quaternion.z());
				
				XsEuler euler = packet.orientationEuler();

				data = data + ",\"roll\":" + to_string(euler.roll());
				data = data + ",\"pitch\":" + to_string(euler.pitch());
				data = data + ",\"yaw\":" + to_string(euler.yaw());
			}

			data = data + "}";
			topic.publish(data);

		}
		XsTime::msleep(0);
	}
	cout << "IMU: Reading stopped" << endl;
	
	control->closePort(mtPort.portName().toStdString());
	control->destruct();
	cout << "IMU: Port closed" << endl;

	return 0;	
};
