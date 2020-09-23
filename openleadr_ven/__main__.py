from openleadr import OpenADRClient
from openleadr.enums import REPORT_TYPE, REPORT_NAME, READING_TYPE, OPT

import random
from datetime import timedelta
from pprint import pprint
from functools import partial

async def main(config):
    """
    Starting point for the client application.
    """
    # Create a new OpenADR client instance
    client = OpenADRClient(ven_name=config['ven_name'],
                           vtn_url=config['vtn_url'],
                           vtn_fingerprint=config.get('vtn_fingerprint'),
                           cert=config.get('cert'),
                           key=config.get('key'),
                           passphrase=config.get('passphrase', ''))

    # Add the event handler
    client.on_event = on_event

    # # Add a report with two resources
    # client.add_report(callable=partial(read_meter, meter_id='meter001'),
    #                   report_id='myreport',
    #                   resource_id='meter001',
    #                   report_name=REPORT_NAME.TELEMETRY_USAGE,
    #                   report_type=REPORT_TYPE.READING,
    #                   reading_type=READING_TYPE.DIRECT_READ,
    #                   sampling_rate=timedelta(seconds=60),
    #                   measurand='power_real',
    #                   unit='W')

    # client.add_report(callable=partial(read_meter, meter_id='meter002'),
    #                   report_id='myreport',
    #                   resource_id='meter002',
    #                   report_name=REPORT_NAME.TELEMETRY_USAGE,
    #                   report_type=REPORT_TYPE.READING,
    #                   reading_type=READING_TYPE.DIRECT_READ,
    #                   sampling_rate=timedelta(seconds=60),
    #                   measurand='power_real',
    #                   unit='W')

    # Run the client
    await client.run()

async def read_meter(meter_id):
    """
    Emulate the collection of a meter reading and return the value. This
    function is called when a report is due.
    """
    print(f"Now collecting value report for meter {meter_id}")
    if meter_id == 'meter001':
        return random.randint(10, 20)
    if meter_id == 'meter002':
        return random.randint(30, 40)

async def on_event(event):
    """
    Handle the event that we receive from the VTN. This coroutine is called when
    an event comes in for this VEN.
    """
    print("Event received:")
    pprint(event)
    return OPT.OPT_IN

if __name__ == "__main__":
    import asyncio
    from argparse import ArgumentParser
    import os
    import yaml
    parser = ArgumentParser()
    parser.add_argument('--config', type=str, default='config.yml')
    args = parser.parse_args()

    with open(args.config) as file:
        config = yaml.safe_load(file.read())
    loop = asyncio.get_event_loop()
    loop.create_task(main(config=config))
    loop.run_forever()