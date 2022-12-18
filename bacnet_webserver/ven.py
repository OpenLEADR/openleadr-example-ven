import asyncio
from datetime import timedelta
from openleadr import OpenADRClient, enable_default_logging

enable_default_logging()

'''
ONE MINUTE EXAMPLE
-ADD IN REPORT VALUE GET REQ TO WEB APP
-ADD IN DEMAND RESP GO and RELEASE GET REQ TO WEB APP
'''

async def collect_report_value():
    # This callback is called when you need to collect a value for your Report
    return 1.23

async def handle_event(event):
    # This callback receives an Event dict.
    # You should include code here that sends control signals to your resources.
    return 'optIn'

# Create the client object
client = OpenADRClient(ven_name='ven123',
                       vtn_url='http://localhost:8080/OpenADR2/Simple/2.0b')

# Add the report capability to the client
client.add_report(callback=collect_report_value,
                  resource_id='device001',
                  measurement='voltage',
                  sampling_rate=timedelta(seconds=10))

# Add event handling capability to the client
client.add_handler('on_event', handle_event)

# Run the client in the Python AsyncIO Event Loop
loop = asyncio.get_event_loop()
loop.create_task(client.run())
loop.run_forever()