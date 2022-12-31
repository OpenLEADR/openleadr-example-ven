import asyncio
from datetime import timedelta
from openleadr import OpenADRClient, enable_default_logging
from datetime import timedelta as td, datetime as dt, timezone as tz
import BAC0
from BAC0.core.devices.local.models import (
    analog_output,
    analog_value,
    binary_value
    )
from BAC0.tasks.RecurringTask import RecurringTask 
from bacpypes.primitivedata import Real

from openadrevent import AdrPayLoad

enable_default_logging()


# create discoverable BACnet object
_new_objects = analog_value(
        name='ADR-Event-Level',
        description='Demand response building kW setpoint',
        presentValue=0,is_commandable=False
    )

# create BACnet app
bacnet = BAC0.lite()
_new_objects.add_objects_to_application(bacnet)
print('BACnet APP Created Success!')


# this is hit when an ADR event comes in
def process_adr_event(event,event_storage):
    print('EVENT HIT!',event)
    signal = event['event_signals'][0]
    intervals = signal['intervals']
    # loop through init DUMMY values for the open ADR payload
    for interval in intervals:
        event_storage.adr_start = interval['dtstart']
        print('adr_start: ',event_storage.adr_start)
        event_storage.adr_payload_value = interval['signal_payload']
        print('adr_payload_value: ',event_storage.adr_payload_value)
        event_storage.adr_duration = interval['duration']
        print('adr_duration: ',event_storage.adr_duration)
        event_storage.adr_event_ends = event_storage.adr_start + event_storage.adr_duration
        print('adr_event_ends: ',event_storage.adr_event_ends)
    

# called by periodic on an interval
def event_checkr():
    global event_storage, bacnet
    
    if event_storage.adr_start != None:
        now_utc = dt.now(tz.utc)
        until_start_time_seconds = (event_storage.adr_start - now_utc).total_seconds()
        until_end_time_seconds = (event_storage.adr_event_ends - now_utc).total_seconds()
        
        if until_start_time_seconds > 0:
            print('TIME TILL EVENT START IN SECONDS: ', round(until_start_time_seconds))
            print('TIME TILL EVENT START IN MINUTES: ', until_start_time_seconds//60)
            print('TIME TILL EVENT START IN HOURS: ', until_start_time_seconds//60//60)

            print('now_utc: ', now_utc)
            print('adr_start: ', event_storage.adr_start)
            print('adr_event_ends: ', event_storage.adr_event_ends)
            adr_sig_object = bacnet.this_application.get_object_name('ADR-Event-Level')        
            print(f'BACNET API SIGNAL IS: {adr_sig_object.presentValue}')
            
        # check if the demand response event is active or not
        elif now_utc >= event_storage.adr_start and now_utc < event_storage.adr_event_ends:
            print('TIME TILL EVENT END IN SECONDS: ', round(until_end_time_seconds))
            print('TIME TILL EVENT END IN MINUTES: ', until_end_time_seconds//60)
            print('TIME TILL EVENT END IN HOURS: ', until_end_time_seconds//60//60)
            
            adr_sig_object = bacnet.this_application.get_object_name('ADR-Event-Level')
            adr_sig_object.presentValue = Real(event_storage.adr_payload_value)            
            print(f'BACNET API SIGNAL IS: {adr_sig_object.presentValue}')
            
        else:
            adr_sig_object = bacnet.this_application.get_object_name('ADR-Event-Level')
            adr_sig_object.presentValue = Real(0)            
            print(f'BACNET API SIGNAL IS: {adr_sig_object.presentValue}')

    else:
        print('NO ADR events have been configured')
        adr_sig_object = bacnet.this_application.get_object_name('ADR-Event-Level')
        adr_sig_object.presentValue = Real(0)            
        print(f'BACNET API SIGNAL IS: {adr_sig_object.presentValue}')

# collect meter reading via BACnet request
# to a fixed device 
async def collect_report_value():
    global bacnet
    # BACnet building power meter
    meter_val = bacnet.read('12345:2 analogInput 2 presentValue')
    return round(meter_val,2)

# called when new event comes in from VTN
async def handle_event(event):
    global event_storage
    process_adr_event(event,event_storage)
    # opt in or out not used
    return 'optIn'


# Create the client object
client = OpenADRClient(ven_name='ven123',
                       vtn_url='http://192.168.0.100:8080/OpenADR2/Simple/2.0b')

# Add the report capability to the client
client.add_report(callback=collect_report_value,
                  resource_id='device001',
                  measurement='power',
                  sampling_rate=timedelta(seconds=10))

# Add event handling capability to the client
client.add_handler('on_event', handle_event)


async def ven_client():
    print('Starting openleadr VEN client')
    # Run the client in the Python AsyncIO Event Loop
    loop = asyncio.get_event_loop()
    loop.create_task(client.run())   
    
    
async def bacnet_worker():
    global bacnet
    print('Starting BACnet API')
    eventcheckr_task = RecurringTask(event_checkr,delay=5)
    eventcheckr_task.start()
    
    while True: # keeps the BACnet script alive
        await asyncio.sleep(.01)


async def main():
    await(asyncio.gather(
        ven_client(), 
        bacnet_worker()
            )
        )


if __name__ == '__main__':
    event_storage = AdrPayLoad()
    asyncio.run(main())
