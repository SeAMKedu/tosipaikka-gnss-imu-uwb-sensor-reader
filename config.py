# MQTT config.
MQTT_HOST = "my-mqtt-server-ip-address"
MQTT_PORT = 1883
MQTT_TOPIC_GPS = "sensorfusion/gps"
MQTT_TOPIC_UWB = "sensorfusion/uwb"

# NTRIP
NTRIP_SERVICE_NAME = "ntrip"
NTRIP_HOST = "my-ntrip-caster-ip-address"
NTRIP_PORT = 2101
NTRIP_AUTH = "my-valid-email-address"
NTRIP_MOUNTPT = "SeAMK"

# u-blox PointPerfect
PP_SERVICE_NAME = "pp"
PP_HOST = "pp.services.u-blox.com"
PP_PORT = 8883
PP_CLIENT_ID = "my-location-thing-id-on-thingstream.io"
PP_TOPIC = "/pp/ip/eu"
PP_CERT_DIR = "cert"

# Allowed values: ntrip, pp
GNSS_CORRECTION_DATA_SERVICE = PP_SERVICE_NAME

"""
(1) Set the IP-address of the MQTT server:

	$ cd /etc/mosquitto/conf.d
	$ sudo nano mosquitto.conf

(2) Run the MQTT server

	$ sudo systemctl stop mosquitto.service
	$ mosquitto -c mosquitto.conf
"""
