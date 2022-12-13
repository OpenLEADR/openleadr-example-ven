import asyncio
from datetime import timedelta
from openleadr import OpenADRClient, enable_default_logging

import BAC0

from BAC0.core.devices.local.models import (
    analog_output,
    analog_value,
    binary_value
    )

from BAC0.tasks.RecurringTask import RecurringTask 
from bacpypes.primitivedata import Real

enable_default_logging()


# create discoverable BACnet object
_new_objects = analog_value(
        name="ADR-Event-Level",
        description="Demand response building kW setpoint",
        presentValue=0,is_commandable=False
    )

     
# create BACnet app
bacnet = BAC0.lite()
_new_objects.add_objects_to_application(bacnet)
bacnet._log.info("APP Created Success!")


# collect meter reading via BACnet request
# to a fixed device 
async def collect_report_value():
    global bacnet
    
    # BACnet building power meter
    meter_val = bacnet.read('12345:2 analogInput 2 presentValue')
    return round(meter_val,2)

# currently not used
async def handle_event(event):
    return 'optIn'


# Create the client object
client = OpenADRClient(ven_name='ven123',
                       vtn_url='http://localhost:8080/OpenADR2/Simple/2.0b')

# Add the report capability to the client
client.add_report(callback=collect_report_value,
                  resource_id='device001',
                  measurement='power',
                  sampling_rate=timedelta(seconds=10))


# Add event handling capability to the client
client.add_handler('on_event', handle_event)



async def ven_client():
    print("Starting client api")
    # Run the client in the Python AsyncIO Event Loop
    loop = asyncio.get_event_loop()
    loop.create_task(client.run())   
    
    
async def bacnet_worker():
    global bacnet
    print("Starting BACnet Api")
    while True:
        await asyncio.sleep(.1)


async def main():
    await(asyncio.gather(
        ven_client(), 
        bacnet_worker()
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
