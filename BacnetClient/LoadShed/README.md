# Load Shed Web App

This is a concept idea for a openLeadr VEN to interact with a BACnet system inside a building for electrical load shed based on the `SIMPLE_SIGNAL` open ADR signal type. 
The ideal building for this app is a larger commercial type and not residential or multi-family. 
Examples of larger buildings in addition to commercial could be hospital, warehouse, school, higher education, laboratory, 
or light commercial smaller-scale business type buildings such as offices, free-standing retail, restaurants, small medical facilities, banks, etc. 
The bottom line is the operations technology (OT) in this app demonstrates BACnet protocol based technology that operates adjustable electrical loads or equipment consuming electrical power.
The concept app supports typical to industry a Modbus protocol electrical main meter read of a report value to send back to the VTN (tested with an eGauge electric meter with Modbus server enabled) and a simple dashboard for building operators to release BACnet overrides applied when the load shed open ADR event is True.
The script executes in a fashion of looping through a list of BACnet addresses and applying the same BACnet point attributes/override to all devices listed in the addresses config file.
An example of this could be a variable volume HVAC system that can consist of dozens of terminal units called VAV boxes where each VAV box would have the same BACnet point attributes (same OT PLC type of program running in each VAV box controller) to globally adjust all zone setpoints at once during the load shed event.
Code can easily be revised to include unique systems and BACnet points if desired.

## Activity Diagram Overview of openLeadr VEN and web dashboard

![pic2](https://raw.githubusercontent.com/bbartling/openleadr-example-ven/main/VenWebApp/LoadShed/images/loadShedActivity.png)

## Installation

```bash
# install python packages with pip
$ pip install -r requirements.txt
```
##  Configuration
The file `config.py` contains basic configurations such as:
* bacnet point details (assumes this is the same for every BACnet devices listed in `ADDRESSES`)
* `WRITE_VAL`: is numeric value to write to the BACnet system for each address in ADDRESSES. I.E., in the case of zone temperature setpoints 80 could represent °F in writing to all terminal units inside the building where global adjusting upwards zone setpoints takes the load off of the chiller or cooling compressors consuming HVAC electrical power. in the base of writing boolean values to the BACnet system BACO syntax for this is `active` or `inactive`.
* `ADDRESSES`: a dictionary of addresses to loop through to apply load shed overrides. The example below represnts MSTP network 123345 hardware address 2
* `LOAD_SHED_GO_VAL`: represents the SIMPLE_SIGNAL value passed from the VTN to VEN to start the load shed process
* `NORMAL_OPERATIONS`: represents the SIMPLE SINGAL value for the BACnet system of "normal" operations or no load shedding
* `MODBUS_METER_ADDRESS`: represents the building utility meter where Modbus protocol is used to retrieve the current electrical power meter reading to report the value back to the VTN. Tested on an [eGauge type](https://www.egauge.net/commercial-energy-monitor/) electric meter with the Modbus server enabled and byteorder=Endian.Big
```
# bacnet point details
OBJECT_TYPE = 'analogValue'
OBJECT_INSTANCE = '302'
PRIORITY = 10

# value to write on load shed to BACnet system devices
WRITE_VAL = 80 

# BACnet addresses to loop through and apply overrides
ADDRESSES = [
        "12345:2","12345:2","12345:2","12345:2","12345:2",
        ]
# open ADR server params
VEN_NAME='ven123'
VTN_URL='http://192.168.0.100:8080/OpenADR2/Simple/2.0b'

# value from VTN to execute load shed
LOAD_SHED_GO_VAL = 1
NORMAL_OPERATIONS = 0

# building main meter MODBUS registries
MODBUS_METER_ADDRESS = '192.168.0.111'
MODBUS_METER_PORT = 502
MODBUS_INPUT_REG = 17
```

##  Run app

```bash
# start the app
$ python client_app.py
```

## BACnet release dashbard
The BACnet release dashboard is a simple html render built on Flask to give a building operators the ability to release overrides implemented through this app when the load shed event started. 
The idea is if BACnet overrides are causing occupant comfort issues or other unwanted hazards to the building systems this simple web dashboard is available to release BACnet overrides and allow systems to go back to normal. 
All overrides when the load shed is over are automatically removed from the dashboard when the load shed event has expired.
* More enhancements can be implemented with typical Flask framework development and VUE.js such as a dashboard page representing the open ADR event, electrical meter report value, and a username/password login if desired.

![pic1](https://raw.githubusercontent.com/bbartling/openleadr-example-ven/main/VenWebApp/LoadShed/images/release_dashboard.PNG)

See BAC0 documention for what is going under the hood of the Flask App:
https://bac0.readthedocs.io/en/latest/

## Author

[linkedin](https://www.linkedin.com/in/ben-bartling-510a0961/)

## Licence

【MIT License】

Copyright 2022 Ben Bartling

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
