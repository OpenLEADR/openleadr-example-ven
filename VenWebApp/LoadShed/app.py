import asyncio
import aiohttp
import threading
from datetime import datetime, timezone, timedelta
from openleadr import OpenADRClient, enable_default_logging
import BAC0

import argparse
import logging
from configs import ADDRESSES, OBJECT_TYPE, OBJECT_INSTANCE, PRIORITY, WRITE_VAL
from configs import MODBUS_INPUT_REG, MODBUS_METER_ADDRESS, MODBUS_METER_PORT
from configs import VTN_URL, VEN_NAME, LOAD_SHED_GO_VAL, NORMAL_OPERATIONS

from models import ReleaseRequestModel
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from dataclasses import dataclass
from flask_pydantic import validate

from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

enable_default_logging()

BASE_DIR = Path(__file__).parent
print(BASE_DIR)
SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(BASE_DIR.joinpath("db.sqlite"))
print(SQLALCHEMY_DATABASE_URI)

db = SQLAlchemy()


@dataclass
class BacnetOverrides(db.Model):

    id: int
    title: str
    date: datetime
    released: bool

    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(140))
    date = db.Column(db.DateTime(), default=datetime.now())
    released = db.Column(db.Boolean(), default=False)

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

    def __repr__(self):
        return f"<BacnetOverrides id: {self.id} - {self.title}"


def make_flask_app():

    def setup_db(app):
        app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.app = app
        db.init_app(app)
        print("Setup DB Success!")

    def db_drop_and_create_all(app):
        with app.app_context():
            db.drop_all()
            db.create_all()
            example1 = BacnetOverrides(
                title="12345:2 analogValue 302 presentValue 55 - 11")
            example2 = BacnetOverrides(
                title="12345:2 analogValue 302 presentValue 55 - 11")
            db.session.add(example1)
            db.session.add(example2)
            db.session.commit()
            BacnetOverridess = BacnetOverrides.query.all()
            print("BacnetOverridess: ", BacnetOverridess)
            print("example1.id: ", example1.id)
            print("example2.id: ", example2.id)
            print(BacnetOverrides.query.all())
            print("DB drop all and create all Success!")

    def add_override_to_db(add_override_str):
        print("INPUTING NEW OVERRIDE INTO DB", add_override_str)
        do = BacnetOverrides(title=add_override_str)
        db.session.add(do)
        db.session.commit()
        print("DB COMMIT SUCCESS!")

    def delete_override_from_db(remove_override_str, override_id):
        print("REMOVING OVERRIDE FROM DB", remove_override_str)
        do = BacnetOverrides.query.filter_by(id=override_id).first()
        db.session.delete(do)
        db.session.commit()
        print("DB COMMIT SUCCESS!")

    def load_shed_start():

        load_shed_start_errors = "success"
        status_str = "no errors occurred writing overrides to the BACnet system"
        for address in ADDRESSES:
            try:
                print("WRITING TO DEVICE: ", address)
                write_str = f"{address} {OBJECT_TYPE} {OBJECT_INSTANCE} presentValue {WRITE_VAL} - {PRIORITY}"
                bacnet.write(write_str)
                add_override_to_db(write_str)
            except Exception as error:
                print(f"write error! {error} on {write_str}")
                load_shed_start_errors = "fail"
                status_str = "errors occurred on writing to BACnet system, see BAC0 logs"

        print("Load shed WRITE status is " + load_shed_start_errors)
        return load_shed_start_errors, status_str

    def load_shed_stop():

        load_shed_stop_errors = "success"
        status_str = "no errors occurred releasing overrides to the BACnet system"

        try:
            BacnetOverridess = BacnetOverrides.query.all()
            print("load_shed_stop BacnetOverridess: ", BacnetOverridess)

            for override in BacnetOverridess:
                release_str = override.title
                temp = release_str.split(" ")
                temp[4] = 'null'  # change the BACnet write val to null for BAC0
                release_str_final = ' '.join(temp)
                print('release_str_final: ', release_str_final)
                bacnet.write(release_str_final)
                delete_override_from_db(release_str_final, override.id)

        except Exception as error:
            print(f"release error! {error} on {release_str}")
            load_shed_stop_errors = "fail"
            status_str = "errors occurred on releasing overrides to BACnet system, see BAC0 logs"

        print("Load shed RELEASE status is " + load_shed_stop_errors)
        return load_shed_stop_errors, status_str

    bacnet = BAC0.lite()
    app = Flask(__name__)
    setup_db(app)
    db_drop_and_create_all(app)

    @app.route("/")
    def index():
        BacnetOverridess = BacnetOverrides.query.all()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(BacnetOverridess)
        return render_template("index.html")

    @app.route("/event-start/")
    def open_adr_event_start():
        status, info = load_shed_start()
        print("EVENT START: ", status + " : ", info)
        ven_client.bacnet_overrides_success = True
        return {"status": status, "info": info}

    @app.route("/event-stop/")
    def open_adr_event_stop():
        status, info = load_shed_stop()
        print("EVENT STOP: ", status + " : ", info)
        ven_client.bacnet_released_success = True
        return {"status": status, "info": info}

    @app.route("/bacnet/release/", methods=["POST"])
    @validate()  # flask pydantic validates browser
    def releaser(body: ReleaseRequestModel):

        try:
            r = request.json
            print("release r: ", r)
            release_str = f'{r["address"]} {r["object_type"]} {r["object_instance"]} presentValue null - {r["priority"]}'
            print("Excecuting release str:", release_str)
            bacnet.write(release_str)
            # remove from sqlite db for dashboard
            delete_override_from_db(release_str, r["id"])
            return jsonify({"status": "success", "point": release_str})
        except Exception as e:
            return jsonify({"status": "error",
                            "point": e}), 500

    return app


class MyVen():

    def __init__(self):
        self.adr_start = None
        self.building_meter = 1.23  # default or error
        self.adr_payload_value = None
        self.adr_duration = None
        self.adr_event_ends = None
        self.adr_event_go = False
        self.adr_event_stop = False
        self.bacnet_overrides_success = False
        self.bacnet_released_success = False

    # this is hit when an ADR event comes in
    def process_adr_event(self, event):
        print("EVENT HIT!", event)
        signal = event["event_signals"][0]
        intervals = signal["intervals"]
        # loop through init DUMMY values for the open ADR payload
        for interval in intervals:
            self.adr_start = interval["dtstart"]
            print("adr_start: ", self.adr_start)
            self.adr_payload_value = interval["signal_payload"]
            print("adr_payload_value: ", self.adr_payload_value)
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

        while not self.bacnet_released_success:
            await self.start_event()
            await self.stop_event()
            await self.event_status()

        print("event_checkr RESET ALL VEN PARAMS")
        self.adr_event_go == False
        self.adr_event_stop == False
        self.bacnet_overrides_success == False
        self.bacnet_released_success == False
        self.adr_payload_value = NORMAL_OPERATIONS

    async def handle_event(self, event):
        """
        Do something based on the event.
        """
        self.process_adr_event(event)
        
        if self.adr_payload_value == LOAD_SHED_GO_VAL:
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
            and self.bacnet_overrides_success == True
            and self.bacnet_released_success == False
        ):
            self.adr_event_stop = True

        else:
            pass


    async def start_event(self):
        if (
            self.adr_event_go == True
            and self.adr_event_stop == False
            and self.bacnet_overrides_success == False
            and self.bacnet_released_success == False
        ):
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:5000/event-start/") as resp:
                    print(await resp.text())

    async def stop_event(self):
        if (
            self.adr_event_go == True
            and self.adr_event_stop == True
            and self.bacnet_overrides_success == True
            and self.bacnet_released_success == False
        ):
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:5000/event-stop/") as resp:
                    print(await resp.text())

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

    args.add_argument("--use-localhost", default=False, action="store_true")
    args.add_argument("--no-localhost", dest="use-localhost",
                      action="store_false")
    args = parser.parse_args()
    if args.use_localhost:
        host_address = "localhost"
        print("Running app on localhost only!")
    else:
        host_address = "0.0.0.0"
    print("Host Address Config For Flask App Is: " + host_address)

    ven_client = MyVen()

    loop = asyncio.get_event_loop()
    loop.create_task(ven_client.make_ven_client().run())
    loop.create_task(ven_client.modbus_meter_reader())

    threaded_asyncio_client = threading.Thread(
        target=lambda: loop.run_forever())
    threaded_asyncio_client.setDaemon(True)
    threaded_asyncio_client.start()

    app = make_flask_app()
    app.run(debug=False, host=host_address,
            port=args.port_number, use_reloader=False)
