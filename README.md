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
1. Update the packages with `sudo apt-get update && sudo apt-get upgrade`, then install the dependencies:<br>
sudo apt-get install git python3-dev python3-pip python3-rpi.gpio<br>
sudo pip3 install -r requirements.txt<br>
1. Optional email configuration
	1. Configure postfix to send mail using Google SMTP, or your ISP's SMTP server
1. Optional twitter configuration
	1. On https://dev.twitter.com/apps/new, create a new application
1. Optional twillio (SMS) configuration
	1. Sign up for a Twilio account at http://www.twilio.com.
1. Copy bin/pi_garage_alert.py to /usr/local/sbin
1. Copy etc/pi_garage_alert_config.py to /usr/local/etc. Edit this file and specify the garage doors you have and alerts you'd like.
1. Copy init.d/pi_garage_alert to /etc/init.d
1. Configure and start the service with<br>
sudo update-rc.d pi_garage_alert defaults<br>
sudo service pi_garage_alert start<br>
1. At this point, the Pi Garage Alert software should be running. You can view its log in /var/log/pi_garage_alert.log

Other Uses
---------------

The script will work with any sensor that can act like a switch. Some alternate uses include:

* Basement or washing machine leak sensors
* Window sensors
