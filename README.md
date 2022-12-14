OpenLEADR Example VEN
=====================

Bare bones BACnet VEN client example with the [BAC0](https://pypi.org/project/BAC0/) Python package. Openleadr VEN provides a discoverable BACnet API with one analog value point to yield the demand response signal passed from the VTN server to VEN client inside the building. Supports a BACnet meter read to send the telemetry data back to the VTN server.


## 1. Install requirements
### ***Python***
```shell
  $ pip install BAC0
 ```


* VEN code example reads electric meter BACnet MSTP device `12345:2 analogInput 2 presentValue`
* One discoverable BACnet object or point named `ADR-Event-Level` would be BACnet discoverable to the buildings control system
* BAC0 is flexible where one could write the control logic or algorithm in Python without a discoverable BACnet API where the VEN could act as a client only BACnet device which would write directly to the control system if the control system cannot support demand response logic or algorithms


## 2. Run app
```shell
  $ python bacnet_server_ven.py
 ```

Debug console yeilds BACnet meter reading values being sent back to the VTN server on 10 second increments.

```shell
Adding 2022-12-13 20:09:30.084739+00:00, 96.46 to report
The number of intervals in the report is now 1
Report will be sent now.
Adding 2022-12-13 20:09:40.110729+00:00, 96.2 to report
The number of intervals in the report is now 1
Report will be sent now.
Adding 2022-12-13 20:09:50.063681+00:00, 95.89 to report
The number of intervals in the report is now 1
Report will be sent now.
Adding 2022-12-13 20:10:00.129581+00:00, 95.57 to report
The number of intervals in the report is now 1
Report will be sent now.
Adding 2022-12-13 20:10:10.099294+00:00, 95.27 to report
The number of intervals in the report is now 1
Report will be sent now.
Adding 2022-12-13 20:10:20.088585+00:00, 94.99 to report
The number of intervals in the report is now 1
Report will be sent now.
Adding 2022-12-13 20:10:30.128590+00:00, 94.67 to report
The number of intervals in the report is now 1
Report will be sent now.
Adding 2022-12-13 20:10:40.097928+00:00, 94.33 to report
The number of intervals in the report is now 1
Report will be sent now.
Adding 2022-12-13 20:10:50.097167+00:00, 94.0 to report
The number of intervals in the report is now 1
Report will be sent now.
 ```

Discoverable BACnet objects tested with the free Comtemporary Controls [BACnet Discovery Tool (BDT)](https://www.ccontrols.com/sd/bdt.htm)