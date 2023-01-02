import asyncio
from datetime import datetime, timezone, timedelta
import pytz
from openleadr import OpenADRServer, enable_default_logging
from functools import partial
import time
from aiohttp import web

import logging
import os

enable_default_logging(logging.DEBUG)

#enable_default_logging()


tz_local = pytz.timezone('America/Chicago')



# convert form data to UTC for openleadr
def convert_to_utc(time, tzname, date=None, is_dst=None):
    tz = pytz.timezone(tzname)
    if date is None: # use date from current local time in tz
        date = datetime.now(tz).date()

    dt = tz.localize(datetime.combine(date, time), is_dst=is_dst)
    return dt.astimezone(pytz.utc), dt.utcoffset().total_seconds()





# Future db
VENS = {
    "ben_house": {"ven_name": "ben_house", "ven_id": "ven_id_ben_house", "registration_id": "reg_id_ben_house"},
    "testven123": {"ven_name": "ven123", "ven_id": "ven_id_ven123", "registration_id": "reg_id_ven123"},
    "volttron_test": {"ven_name": "volttron_test", "ven_id": "ven_id_volttron_test", "registration_id": "reg_id_volttron_test"}     
}


# form data lookup for creating an event with the html page
def find_ven(form_data):
    for v in VENS.values():
        print(v['ven_id'])
        if v.get('ven_id') == form_data:
            return True
        else:
            return False

'''
OPEN LEADR CONFIG
'''

async def on_create_party_registration(registration_info):
    """
    Inspect the registration info and return a ven_id and registration_id.

    print("TRYING TO LOOK UP VEN FOR REGISTRATION: ",registration_info['ven_name'])

    ven_name = registration_info['ven_name']
    for v in VENS.values():
        #print(values['ven_name'])
        if v.get('ven_name') == ven_name:
            print(f"REGISTRATION SUCCESS WITH NAME:  {v.get('ven_name')} FROM PAYLOAD, MATCH FOUND {ven_name}")
            return v['ven_id'],v['registration_id']
        else:
            print("REGISTRATION FAIL BAD VEN NAME: ",registration_info['ven_name'])
            return False

    """
    if registration_info['ven_name'] == 'ven123':
        ven_id = 'ven_id_123'
        registration_id = 'reg_id_123'
        return ven_id, registration_id
    else:
        return False

 
async def on_register_report(ven_id, resource_id, measurement, unit, scale,
                             min_sampling_interval, max_sampling_interval):
    """
    Inspect a report offering from the VEN and return a callback and sampling interval for receiving the reports.
    """
    callback = partial(on_update_report, ven_id=ven_id, resource_id=resource_id, measurement=measurement)
    sampling_interval = min_sampling_interval
    return callback, sampling_interval

async def on_update_report(data, ven_id, resource_id, measurement):
    """
    Callback that receives report data from the VEN and handles it.
    """
    for time, value in data:
        print(f"Ven {ven_id} reported {measurement} = {value} at time {time} for resource {resource_id}")

async def event_response_callback(ven_id, event_id, opt_type):
    """
    Callback that receives the response from a VEN to an Event.
    """
    print(f"VEN {ven_id} responded to Event {event_id} with: {opt_type}")




async def handle_cancel_event(request):
    """
    Handle a cancel event request.
    """
    try:
        server = request.app["server"]
        server.cancel_event(ven_id='ven_id_ben_house',
            event_id="our-event-id",
        )


        datetime_local = datetime.now(tz_local)
        datetime_local_formated = datetime_local.strftime("%H:%M:%S")     
        info = f"Event canceled now, local time: {datetime_local_formated}"
        response_obj = { 'status' : 'success', 'info': info }
        
        ## return sucess
        return web.json_response(response_obj)

    except Exception as e:

        response_obj = { 'status' : 'failed', 'info': str(e) }
        
        ## return failed with a status code of 500 i.e. 'Server Error'
        return web.json_response(response_obj, status=500)




async def handle_trigger_event(request):
    """
    Handle a trigger event request.
    """
    try:
        duration = request.match_info['minutes_duration']
        
        server = request.app["server"]
        server.add_event(ven_id='ven_id_123',
            signal_name='SIMPLE',
            signal_type='level',
            intervals=[{#'dtstart': datetime.now(timezone.utc),
                        'dtstart': datetime.now(timezone.utc) + timedelta(seconds=100),
                        'duration': timedelta(minutes=int(duration)),
                        'signal_payload': 1.0}],
            callback=event_response_callback,
            event_id="our-event-id",
        )

        datetime_local = datetime.now(tz_local)
        datetime_local_formated = datetime_local.strftime("%H:%M:%S")     
        info = f"Event added now, local time: {datetime_local_formated}"
        response_obj = { 'status' : 'success', 'info': info }
        
        ## return sucess
        return web.json_response(response_obj)
        

    except Exception as e:

        response_obj = { 'status' : 'failed', 'info': str(e) }
        ## return failed with a status code of 500 i.e. 'Server Error'
        return web.json_response(response_obj, status=500)




async def all_ven_info(request):
    """
    Handle a trigger event request.
    """
    try:

        return web.json_response(VENS)
        

    except Exception as e:
        ## Bad path where name is not set
        response_obj = { 'status' : 'failed', 'info': str(e) }
        ## return failed with a status code of 500 i.e. 'Server Error'
        return web.json_response(response_obj, status=500)


'''
APP CONFIG
'''


# Create the server object
server = OpenADRServer(vtn_id='cloudvtn',
                        http_host='0.0.0.0',
                        #ven_lookup=ven_lookup_function
                        )



# Add the handler for client (VEN) registrations
server.add_handler('on_create_party_registration', on_create_party_registration)
# Add the handler for report registrations from the VEN
server.add_handler('on_register_report', on_register_report)

server.app.add_routes([
    web.get('/trigger/{minutes_duration}', handle_trigger_event),
    web.get('/cancel', handle_cancel_event),
    web.get('/vens', all_ven_info)
])



# Run the server on the asyncio event loop
loop = asyncio.get_event_loop()
loop.create_task(server.run())
loop.run_forever()




