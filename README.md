# PagerDuty Alerts xBar

Welcome! I wrote this script to provide quick access to PagerDuty notification events, as well as another audible/visual notification when a new incident is created.

Original Repository: https://github.com/sirgatez/PagerDuty_Alerts_xBar

## Description

A simple xBar application to provide a list of incidents, popup notifications, and audible alerts for new triggered incidents.

## Getting Started

### Dependencies

* Python 3.x

* One of the following
	* Argos (Linux) https://github.com/p-e-w/argos
	* SwiftBar (MacOS) https://github.com/swiftbar/SwiftBar
	* xBar (MacOS) (Formally BitBar) https://github.com/matryer/xbar/

* Python Libraries - Minimium:
	* pytz
	* requests

* Python Libraries - Mac Optional
	* pyobjc

* Python Libraries - Linux Optional
	* Notify

* External requirements (Optional)
	* Mac: afplay (included with MacOS)
	* Linux: sox, libsox-fmt-mp3

### Installing Python Dependancies

pip3 install requests
pip3 install pytz

pip3 install pyobjc  # Optional

### Installing

Copy the contents of XBarApps (scripts and folders) into your xBar Plugins folder.

### Executing program

xBar will automatically pickup the new scripts and begin executing them once they are copied into the plugins folder.

## Help

If you encounter any problems or have any suggestions for improvements please don't hesitate to post and issue or submit a pull request.

## Authers

Joshua Briefman (https://www.linkedin.com/in/sirgatez/) [sirgatez at gmail dot com]

## Version History

* 0.1 Initial public release

## License

Please review the included LICENSE file for the contents of this repository.
