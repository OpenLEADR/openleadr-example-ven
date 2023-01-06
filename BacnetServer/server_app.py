import asyncio
import aiohttp
import threading
from datetime import datetime, timezone, timedelta
from openleadr import OpenADRClient, enable_default_logging

import BAC0
from BAC0.tasks.RecurringTask import RecurringTask 
from bacpypes.primitivedata import Real
from BAC0.core.devices.local.models import (
    analog_output,
    analog_value,
    binary_value
    )

import argparse
import logging
from configs import MODBUS_METER_ADDRESS, MODBUS_METER_PORT, MODBUS_INPUT_REG
from configs import VTN_URL, VEN_NAME, NORMAL_OPERATIONS

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

from pathlib import Path
from dataclasses import dataclass
from flask_pydantic import validate

from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

enable_default_logging()


def make_bacnet_app():
    
    def check_event_status():
    
        adr_sig_object = bacnet.this_application.get_object_name('ADR-Event-Level')
        adr_sig_object.presentValue = Real(ven_client.bacnet_api_payload_value)            

    # create discoverable BACnet object
    _new_objects = analog_value(
            name='ADR-Event-Level',
            description='SIMPLE SIGNAL demand response level',
            presentValue=0,is_commandable=False
        )

    # create BACnet app
    bacnet = BAC0.lite()
    _new_objects.add_objects_to_application(bacnet)
    print('BACnet APP Created Success!')
    
    bacnet_sig_handle = RecurringTask(check_event_status,delay=5)
    bacnet_sig_handle.start()
    
    return bacnet


def make_flask_app():

    app = Flask(__name__)

    @app.route("/")
    def index():
        info = {              
                "adr_start": ven_client.adr_start,
                "building_meter": ven_client.building_meter,
                "adr_duration": ven_client.adr_duration,
                "adr_event_ends": ven_client.adr_event_ends,
                "adr_event_is_active": ven_client.adr_event_is_active,
                "event_payload_value": ven_client.event_payload_value,
                "bacnet_api_payload_value": ven_client.bacnet_api_payload_value
            }
        return render_template("index.html", event_info=info)

    @app.route("/adr-signal/")
    def adr_sig():
        return {"status": "status", "info": ven_client.event_payload_value}

    return app


class MyVen():

    def __init__(self):
        self.adr_start = "Not Set"
        self.building_meter = 1.23  # default or error
        self.adr_duration = "Not Set"
        self.adr_event_ends = "Not Set"
        self.event_payload_value = "Not Set"
        self.bacnet_api_payload_value = NORMAL_OPERATIONS
        self.adr_event_is_active = False
        self.last_scan = datetime.now(timezone.utc)

    # this is hit when an ADR event comes in
    def process_adr_event(self, event):
        print("EVENT HIT!", event)
        signal = event["event_signals"][0]
        intervals = signal["intervals"]
        # loop through init DUMMY values for the open ADR payload
        for interval in intervals:
            self.adr_start = interval["dtstart"]
            print("adr_start: ", self.adr_start)
            self.event_payload_value = interval["signal_payload"]
            print("event_payload_value: ", self.event_payload_value)
            self.adr_duration = interval["duration"]
            print("adr_duration: ", self.adr_duration)
            self.adr_event_ends = self.adr_start + self.adr_duration
            print("adr_event_ends: ", self.adr_event_ends)

    async def collect_report_value(self):
        await asyncio.gather(
            asyncio.to_thread(modbus_meter_reader),
            asyncio.sleep(1))


    def modbus_meter_reader(self):

        try:
            client = ModbusTcpClient(MODBUS_METER_ADDRESS,
                                     port=MODBUS_METER_PORT)
            
            result = client.read_input_registers(MODBUS_INPUT_REG,
                                                 2,
                                                 units=1)
            #print(result.registers)
            decoder = BinaryPayloadDecoder.fromRegisters(result.registers, 
                                                         byteorder=Endian.Big)
            building_meter = round(decoder.decode_32bit_float(),3)
            print("MODBUS electric meter read: ", building_meter)
            self.building_meter = building_meter
            client.close()
            return building_meter

        except:
            print("ERROR ON MODBUS METER READ")
            client.close()
            self.building_meter = 1.23

    async def event_do(self,delay,item):
        await asyncio.sleep(delay)
        
        if item == "go":
            print("EVENT GO!")
            self.adr_event_is_active = True
            self.bacnet_api_payload_value = self.event_payload_value
            
        elif item == "stop":
            print("EVENT STOP!")
            self.adr_event_is_active = False
            self.bacnet_api_payload_value = NORMAL_OPERATIONS
            self.adr_start = "Event has expired"
            self.adr_duration = "Event has expired"
            self.adr_event_ends = "Event has expired"
            self.event_payload_value = "Event has expired"

    async def event_checkr(self):
        now_utc = datetime.now(timezone.utc)
        until_start_time_seconds = (
            self.adr_start - now_utc).total_seconds()
        until_end_time_seconds = (
            self.adr_start - self.adr_event_ends).total_seconds()
        
        await self.event_do(until_start_time_seconds,
                            'go')
        await self.event_do(until_start_time_seconds+until_end_time_seconds,
                            'stop')
        
        
    async def handle_event(self, event):
        """
        Do something based on the event.
        """
        self.process_adr_event(event)
        loop = asyncio.get_event_loop()
        loop.create_task(self.event_checkr())
        return "optIn"


    def make_ven_client(self):
        client = OpenADRClient(ven_name=VEN_NAME,
                               vtn_url=VTN_URL)
        client.add_report(callback=self.modbus_meter_reader,
                          resource_id='main_meter',
                          measurement='power',
                          sampling_rate=timedelta(seconds=10))
        client.add_handler('on_event', self.handle_event)
        return client


if __name__ == "__main__":
    print("Starting main loop")
    parser = argparse.ArgumentParser(add_help=False)
    args = parser.add_argument_group("Options")
    args.add_argument("-port",
                      "--port_number",
                      required=False,
                      type=int,
                      default=5000,
                      help="Port number to run web app")

    
    args.add_argument("--use-bacnet", default=False, action="store_true")
    args.add_argument("--no-bacnet", dest="use-bacnet",
                      action="store_false")
    
    args.add_argument("--use-openadr", default=False, action="store_true")
    args.add_argument("--no-openadr", dest="use-openadr",
                      action="store_false") 
    
    args = parser.parse_args()
    print("use_bacnet: ",args.use_bacnet)
    print("use_openadr: ",args.use_openadr)

    ven_client = MyVen()

    if args.use_openadr:
        loop = asyncio.get_event_loop()
        
        loop.create_task(ven_client.make_ven_client().run())
        t1 = threading.Thread(
            target=lambda: loop.run_forever())
        t1.setDaemon(True)
        t1.start()
    
    if args.use_bacnet:
        t2 = threading.Thread(
            target=lambda: make_bacnet_app())
        t2.setDaemon(True)
        t2.start()

    flask_app = make_flask_app()
    flask_app.run(debug=False, host="0.0.0.0",
            port=args.port_number, use_reloader=False)