Pi Garage Alert
===============

Raspberry Pi Python script to email or send an SMS if a garage door is left open.


Quick Start
---------------

This is a heavily condensed quick start guide. New users are strongly encouraged to read the original full documentation: [Part 1](https://web.archive.org/web/20230406173732/https://www.richlynch.com/2013/07/27/pi_garage_alert_1/), [Part 2](https://web.archive.org/web/20230311070645/https://www.richlynch.com/2013/08/04/pi_garage_alert_2/)
 
1. Equipment required
	1. Raspberry Pi model
	1. 2GB or larger SD card for the RPi filesystem
	1. Magnetic sensor (e.g. https://www.amazon.com/dp/B005H3GCW0)
	1. USB wifi adapter (if not using Ethernet and your RPi does not have built-in wireless)
	1. USB power supply for RPi
1. Connect one wire of the magnetic sensor to a GPIO pin on the RPi and the other to a ground pin on the RPi. Putting a 1kohm resistor in series with the sensor can help protect the RPi from damage if anything is misconfigured.
1. Set up the Raspberry Pi: https://www.raspberrypi.com/documentation/computers/getting-started.html#installing-the-operating-system
1. Update the packages with `sudo apt-get update && sudo apt-get upgrade`
1. Install the RPi packages: `sudo apt-get install git python3-dev python3-pip python3-rpi.gpio`
1. Edit `etc/pi_garage_alert_config.py` to specify garage doors and alerts
1. Setup the Python app:
	1. `[sudo] mkdir /usr/local/sbin/pi_garage_alert`
	1. `[sudo] cp bin/pi_garage_alert.py /usr/local/sbin/pi_garage_alert`
	1. `[sudo] cp requirements.txt /usr/local/sbin/pi_garage_alert`
	1. `[sudo] cp init.d/pi_garage_alert /etc/init.d/`
	1. `[sudo] cp etc/pi_garage_alert_config.py /usr/local/etc/`
	1. `[sudo] chown pi /usr/local/etc/pi_garage_alert_config.py`
1. Install Python dependencies:
	1. `[sudo] chown pi -R /usr/local/sbin/pi_garage_alert`
	1. `cd /usr/local/sbin/pi_garage_alert`
	1. `[sudo] python3 -m venv venv`
	1. `source venv/bin/activate`
	1. `pip3 install -r requirements.txt`
1. Optional email configuration
	1. Configure postfix to send mail using an SMTP server
1. Optional twitter configuration
	1. On https://dev.twitter.com/apps/new, create a new application
1. Optional twillio (SMS) configuration
	1. Sign up for a Twilio account at http://www.twilio.com.
1. Configure and start the service:
	1. `sudo update-rc.d pi_garage_alert defaults`
	1. `sudo service pi_garage_alert start`
1. The Pi Garage Alert software should be running. View its log in `/var/log/pi_garage_alert.log`

Other Uses
---------------

The script will work with any sensor that can act like a switch. Some alternate uses include:

* Basement or washing machine leak sensors
* Window sensors
