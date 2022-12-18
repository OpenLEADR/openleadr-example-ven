
import BAC0,time
from flask import Flask, request, jsonify
import flask
import logging
import argparse
from datetime import datetime
from threading import Thread
import random #for testing meter reader

#logging.basicConfig(filename='_log_flask.log', level=logging.WARNING)

#STATIC_BACNET_IP = '192.168.0.103/24'
#bacnet = BAC0.lite(IP=STATIC_BACNET_IP)

bacnet = BAC0.lite()


#start flask app
app = Flask(__name__)

# future will be release overrides made by web app
OVERRIDES = []
METER_VALUE = None


def meter_reader_task():
    global METER_VALUE
    
    while True:
        METER_VALUE = random.randint(50, 100)
        print('meter reader: ',METER_VALUE)
        time.sleep(30)
        

#READ
@app.route('/bacnet/read/', methods=['GET'])
def reader():

    try:
        json_data = flask.request.json
        address = json_data["address"]
        object_type = json_data["object_type"]
        object_instance = json_data["object_instance"]

        read_vals = f'{address} {object_type} {object_instance} presentValue'
        print("Excecuting read_vals statement:", read_vals)
        read_result = bacnet.read(read_vals)
        response_obj = round(read_result,2)
        
    except Exception as error:
        logging.error("Error trying BACnet Read {}".format(error))
        info = str(error)
        print(error)
        response_obj = {'read error' : info}
        return jsonify(response_obj), 500

    return jsonify(response_obj)


#WRITE
@app.route('/bacnet/write/', methods=['GET'])
def writer():
    
    '''
    ADD TO OVERRIDES []
    '''

    try:
        json_data = flask.request.json
        address = json_data["address"]
        object_type = json_data["object_type"]
        object_instance = json_data["object_instance"]
        value = json_data["value"]
        priority = json_data["priority"]
    
        write_vals = f'{address} {object_type} {object_instance} presentValue {value} - {priority}'
        print("Excecuting write_vals statement:", write_vals)
        bacnet.write(write_vals)
        response_obj = {'write success'}
        
    except Exception as error:
        logging.error("Error trying BACnet Write {}".format(error))
        info = str(error)
        print(error)
        response_obj = {'write error' : info}
        return jsonify(response_obj), 500

    return jsonify(response_obj)


#RELEASE
@app.route('/bacnet/release/', methods=['GET'])
def releaser():
    
    '''
    REMOVE FROM OVERRIDES []
    '''

    try:
        json_data = flask.request.json
        address = json_data["address"]
        object_type = json_data["object_type"]
        object_instance = json_data["object_instance"]
        priority = json_data["priority"]
    
        write_vals = f'{address} {object_type} {object_instance} presentValue null - {priority}'
        print("Excecuting write_vals statement:", write_vals)
        bacnet.write(write_vals)
        info = f'BACnet point release to device'
        response_obj = {'success'}
        
    except Exception as error:
        logging.error("Error trying BACnet Release {}".format(error))
        info = str(error)
        print(error)
        response_obj = {'release error' : info}
        return jsonify(response_obj), 500

    return jsonify(response_obj)


#BACnet OVERRIDES, future html to release overrides made by app
@app.route('/bacnet', methods=['GET'])
def overrides():
    return jsonify(OVERRIDES)


#HOME future route to hit from VEN APP
@app.route('/load-shed-go', methods=['GET'])
def demand_response_go():
    
    '''
    RUN FUTURE DEMAND RESPONSE ALGORITHM
    LOAD SHED ONLY FROM OPEN LEADR VEN
    TO WRITE VIA BACNET TO HVAC OR OTHER
    '''
    return jsonify(datetime.utcnow().isoformat())


#HOME future route to hit from VEN APP
@app.route('/load-shed-release', methods=['GET'])
def demand_response_release():
    
    '''
    RUN FUTURE DEMAND RESPONSE ALGORITHM
    LOAD SHED RELEASE HIT FROM OPEN LEADR WHEN EVENT EXPIRES
    TO RELEASE VIA BACNET TO HVAC OR OTHER
    '''
    return jsonify(datetime.utcnow().isoformat())


#HOME future route to hit from VEN APP
@app.route('/meter', methods=['GET'])
def meter_reader():
    
    '''
    FOR OPEN LEADR VEN REPORT
    OF POWER METER VALUE
    Modbus or BACnet electric meter
    reocccuring task on a seperate thread
    to get meter value
    '''
    
    return jsonify(METER_VALUE)


#HOME future login page
@app.route('/', methods=['GET'])
def index():
    return jsonify(datetime.utcnow().isoformat())



if __name__ == '__main__':
    print("Starting main loop")
    thread = Thread(target=meter_reader_task)
    thread.daemon = True
    thread.start()

    my_parser = argparse.ArgumentParser(description='Run Flask App as localhost or seperate device')
    my_parser.add_argument('-ip',
                           '--host_address',
                           required=False,
                           type=str,
                           default='0.0.0.0',
                           help='Default is to run app on a seperate device. To run as localhost try: python3 flaskapp.py -ip localhost')
    args = my_parser.parse_args()

    host_address = args.host_address
    print('Host IP Address Config for the Flask App Is ' + host_address)

    #app.run(debug=False,port=5000,host=host_address,use_reloader=False)
    app.run(debug=False,port=5000,host=host_address)

