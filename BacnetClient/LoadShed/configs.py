

# bacnet point details
OBJECT_TYPE = 'analogValue'
OBJECT_INSTANCE = '302'
PRIORITY = 10

# value to write on load shed to BACnet system devices
WRITE_VAL = 80 

# BACnet addresses to loop through and apply overrides
ADDRESSES = [
        "12345:2","12345:2","12345:2","12345:2","12345:2",
        ]
# open ADR server params
VEN_NAME='ven123'
VTN_URL='http://192.168.0.100:8080/OpenADR2/Simple/2.0b'

# value from VTN to execute load shed
LOAD_SHED_GO_VAL = 1
NORMAL_OPERATIONS = 0

# building main meter MODBUS registries
MODBUS_METER_ADDRESS = '192.168.0.111'
MODBUS_METER_PORT = 502
MODBUS_INPUT_REG = 17
    

    
