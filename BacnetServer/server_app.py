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
from configs import MODBUS_METER_ADDRESS, MODBUS_METER_PORT
from configs import VTN_URL, VEN_NAME, LOAD_SHED_GO_VAL ,NORMAL_OPERATIONS

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
        adr_sig_object.presentValue = Real(ven_client.bacnet_payload_value)            
        #print(f'BACNET API SIGNAL IS: {adr_sig_object.presentValue}')
                
        if ven_client.bacnet_payload_value != NORMAL_OPERATIONS:
            ven_client.bacnet_sig_change_success = True
            print(f'bacnet_sig_change_success = True')
            
        if (
            ven_client.bacnet_payload_value == NORMAL_OPERATIONS
            and ven_client.bacnet_sig_change_success == True
        ):
            ven_client.bacnet_sig_revert_success = True
            print('bacnet_sig_revert_success = True')

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
    
    bacnet_sig_handle = RecurringTask(check_event_status,delay=5)
    bacnet_sig_handle.start()
    
    return bacnet


def make_flask_app():

    app = Flask(__name__)

    @app.route("/")
    def index():
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return open_adr_event_stop()
        return render_template("index.html")

    @app.route("/adr-signal/")
    def adr_sig():
        return {"status": "status", "info": 0}

    def open_adr_event_stop():
        return {"status": "status", "info": "info"}

    return app


class MyVen():

    def __init__(self):
        self.adr_start = None
        self.building_meter = 1.23  # default or error
        self.adr_duration = None
        self.adr_event_ends = None
        self.event_payload_value = None
        self.bacnet_payload_value = NORMAL_OPERATIONS
        self.adr_event_go = False
        self.adr_event_stop = False
        self.bacnet_sig_change_success = False
        self.bacnet_sig_revert_success = False

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
        return self.building_meter


    async def modbus_meter_reader(self):

        try:
            
            client = ModbusTcpClient(MODBUS_METER_ADDRESS,
                                     port=MODBUS_METER_PORT)
            result = client.read_input_registers(500,2,units=1)
            print(result.registers)
            decoder = BinaryPayloadDecoder.fromRegisters(result.registers, 
                                                         byteorder=Endian.Big)
            data = decoder.decode_32bit_float()
            print("MODBUS electric meter read: ", data)
            self.building_meter = round(data,3)
            client.close()

        except:
            print("ERROR ON MODBUS METER READ")
            client.close()
            self.building_meter = 1.23

        await asyncio.sleep(30)

    async def event_checkr(self):  # datetime, timezone, timedelta

        while not self.bacnet_sig_revert_success:
            await self.start_event()
            await self.stop_event()
            await self.event_status()

        print("event_checkr RESET ALL VEN PARAMS")


    async def handle_event(self, event):
        """
        Do something based on the event.
        """
        self.process_adr_event(event)
        loop = asyncio.get_event_loop()
        loop.create_task(self.event_checkr())
        return "optIn"

    async def event_status(self):
        now_utc = datetime.now(timezone.utc)

        until_start_time_seconds = (
            self.adr_start - now_utc).total_seconds()

        until_end_time_seconds = (
            self.adr_event_ends - now_utc).total_seconds()

        if until_start_time_seconds > 0:
            # if (now_utc - datetime.now(timezone.utc)).total_seconds() % 10 == 0:
            print("TIME UNTIL EVENT START IN SECONDS: ",
                  round(until_start_time_seconds))
            print("TIME UNTIL EVENT START IN MINUTES: ",
                  until_start_time_seconds//60)
            print("TIME UNTIL EVENT START IN HOURS: ",
                  until_start_time_seconds//60//60)
            await asyncio.sleep(15)

        # check if the demand response event is active or not
        elif now_utc >= ven_client.adr_start and now_utc < ven_client.adr_event_ends:
            self.adr_event_go = True
            # if (now_utc - datetime.now(timezone.utc)).total_seconds() % 10 == 0:
            print("TIME UNTIL EVENT END IN SECONDS: ",
                  round(until_end_time_seconds))
            print("TIME UNTIL EVENT END IN MINUTES: ",
                  until_end_time_seconds//60)
            print("TIME UNTIL EVENT END IN HOURS: ",
                  until_end_time_seconds//60//60)
            await asyncio.sleep(15)

        elif (
            now_utc > ven_client.adr_event_ends
            and self.adr_event_go == True
            and self.adr_event_stop == False
            and self.bacnet_sig_change_success == True
            and self.bacnet_sig_revert_success == False
        ):
            self.adr_event_stop = True

        else:
            pass


    async def start_event(self):
        if (
            self.adr_event_go == True
            and self.adr_event_stop == False
            and self.bacnet_sig_change_success == False
            and self.bacnet_sig_revert_success == False
        ):
            self.bacnet_payload_value = LOAD_SHED_GO_VAL

    async def stop_event(self):
        if (
            self.adr_event_go == True
            and self.adr_event_stop == True
            and self.bacnet_sig_change_success == True
            and self.bacnet_sig_revert_success == False
        ):
            self.bacnet_payload_value = NORMAL_OPERATIONS



    def make_ven_client(self):
        client = OpenADRClient(ven_name=VEN_NAME,
                               vtn_url=VTN_URL)
        client.add_report(callback=self.collect_report_value,
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

    args.add_argument("--use-modbusmeter", default=False, action="store_true")
    args.add_argument("--no-modbusmeter", dest="use-modbusmeter",
                      action="store_false") 
    
    args = parser.parse_args()

    ven_client = MyVen()

    loop = asyncio.get_event_loop()
    loop.create_task(ven_client.make_ven_client().run())
    loop.create_task(ven_client.modbus_meter_reader())

    t1 = threading.Thread(
        target=lambda: loop.run_forever())
    t1.setDaemon(True)
    t1.start()
    
    t2 = threading.Thread(
        target=lambda: make_bacnet_app())
    t2.setDaemon(True)
    t2.start()

    flask_app = make_flask_app()
    flask_app.run(debug=False, host="0.0.0.0",
            port=args.port_number, use_reloader=False)
