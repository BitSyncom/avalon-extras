#!/usr/bin/env python2.7

from __future__ import division
from serial import Serial
from optparse import OptionParser
import binascii
import sys
import time
import math

parser = OptionParser()
parser.add_option("-s", "--serial", dest="serial_port", default="/dev/ttyUSB0", help="Serial port")
parser.add_option("-c", "--choose", dest="is_rig", default="0", help="0 Is For Rig Testing")
(options, args) = parser.parse_args()

ser = None
try:
    ser = Serial(options.serial_port, 115200, 8, timeout=0.2) # 1 second
except Exception as e:
    print str(e)

PMU871_TYPE = ( 'PMU871' )

PMU871_VER = ( '8C' )

PMU871_PG  = { 'pg_good': '0001', 'pg_bad': '0002' }

PMU871_LED = { 'led_close': '0000', 'led_green': '0001', 'led_red': '0002' }

#ntc: check the table(Thick Film Chip NTC Thermistor Devices_CMFA103J3500HANT.pdf)
#v12_l/h(Vin) equation: x * 3.3 / 4095 = (11~14) * 5.62 / 25.62
#vcore_l/h(Vout) equation: x * 3.3 / 4095 = (8.2~8.7) * 20 / 63
PMU871_ADC = { 'ntc_l': 524, 'ntc_h': 9615, 'v12_l':2994, 'v12_h': 3810, 'vcore_l': 3600, 'vcore_h': 4300}

error_message = {
    'serial_port': 'Connection failed.',
    'ntc_1': 'NTC_1 value error.',
    'v12': 'V12 value error.',
    'vcore_1': 'VCORE1 value error.',
    'vcore_2': 'VCORE2 value error.',
    'vcore_3': 'VCORE3 value error.',
    'pg_1' : 'PG1 value error.',
    'pg_2' : 'PG2 value error.' ,
    'pg_3' : 'PG3 value error.' ,
    'led_1': 'LED1 status error.',
    'led_2': 'LED2 status error.',
    'led_3': 'LED3 status error.',
    'ntc_max': 'NTC_MAX value error.'
}

def CRC16(message):
    #CRC-16-CITT poly, the CRC sheme used by ymodem protocol
    poly = 0x1021
    #16bit operation register, initialized to zeros
    reg = 0x0000
    #pad the end of the message with the size of the poly
    message += '\x00\x00'
    #for each bit in the message
    for byte in message:
        mask = 0x80
        while(mask > 0):
            #left shift by one
            reg<<=1
            #input the next bit from the message into the right hand side of the op reg
            if ord(byte) & mask:
                reg += 1
            mask>>=1
            #if a one popped out the left of the reg, xor reg w/poly
            if reg > 0xffff:
                #eliminate any one that popped out the left
                reg &= 0xffff
                #xor with the poly, this is the remainder
                reg ^= poly
    return reg

def mm_package(cmd_type, idx = "01", cnt = "01", module_id = None, pdata = '0'):
    if module_id == None:
        data = pdata.ljust(64, '0')
    else:
        data = pdata.ljust(60, '0') + module_id.rjust(4, '0')
    crc = CRC16(data.decode("hex"))
    return "434E" + cmd_type + "00" + idx + cnt + data + hex(crc)[2:].rjust(4, '0')

def show_help():
    print("\
h: Help\n\
1: Detect The PMU Version\n\
2: Set	  The PMU Output Voltage\n\
          |-----------------------|---------------------|\n\
          |   008000018000028000  |       9.78V         |\n\
          |-----------------------|---------------------|\n\
3: Set    The PMU Led State\n\
          |---------------------------------------------|\n\
          |     Setting           |      Led state      |\n\
          |-----------------------|---------------------|\n\
          |   000000010000020000  |   All   Led Off     |\n\
          |-----------------------|---------------------|\n\
          |   000001010001020001  |   Green Led On      |\n\
          |-----------------------|---------------------|\n\
          |   000002010002020002  |   Red   Led On      |\n\
          |-----------------------|---------------------|\n\
          |   000004010004020004  |   Green Led Blink   |\n\
          |-----------------------|---------------------|\n\
          |   000008010008020008  |   Red   Led Blink   |\n\
          |-----------------------|---------------------|\n\
4: Get    The PMU State\n\
q: Quit\n")

def detect_version():
    global PMU_TYPE
    global PMU_ADC
    global PMU_LED
    global PMU_PG

    input_str = mm_package("10", module_id = None)
    ser.flushInput()
    ser.write(input_str.decode('hex'))
    res = ser.readall()
    if res == "":
        print (error_message['serial_port'])
        return False
    PMU_DNA = binascii.hexlify(res[6:14])
    if res[14:16] == PMU871_VER:
        PMU_TYPE = PMU871_TYPE
        PMU_VER = res[14:29]
        PMU_ADC = PMU871_ADC
        PMU_LED = PMU871_LED
        PMU_PG  = PMU871_PG
    else:
        print(res[14:29])
        print("Invalid PMU version")
        return False

    print(PMU_TYPE + " VER:" + PMU_VER)
    print(PMU_TYPE + " DNA:" + PMU_DNA)
    return True

def judge_vol_range(vol):
    if len(vol) != 18:
        return False
    if (vol[0:2] != "00") and (vol[6:8] != "01") and (vol[12:14] != "02"):
        return False

    return True

def judge_led_range(led):
    if len(led) != 18:
        return False
    if (led[0:2] != "00") and (led[6:8] != "01") and (led[12:14] != "02"):
        return False

    return True

def judge_ntc_range(ntc):
    if len(ntc) != 6:
        return False
    return True

def set_vol_value(vol_value):
    if judge_vol_range(vol_value) == True:
        input_str = mm_package("22", idx = vol_value[0:2], module_id = None, pdata = vol_value[2:6]);
        ser.flushInput()
        ser.write(input_str.decode('hex'))
        input_str = mm_package("22", idx = vol_value[6:8], module_id = None, pdata = vol_value[8:12]);
        ser.flushInput()
        ser.write(input_str.decode('hex'))
        input_str = mm_package("22", idx = vol_value[12:14], module_id = None, pdata = vol_value[14:18]);
        ser.flushInput()
        ser.write(input_str.decode('hex'))
    else:
        print("Bad voltage vaule!")

def set_led_state(led):
    if judge_led_range(led) == True:
        input_str = mm_package("24", idx = led[0:2], module_id = None, pdata = led[2:6]);
        ser.flushInput()
        ser.write(input_str.decode('hex'))
        input_str = mm_package("24", idx = led[6:8], module_id = None, pdata = led[8:12]);
        ser.flushInput()
        ser.write(input_str.decode('hex'))
        input_str = mm_package("24", idx = led[12:14], module_id = None, pdata = led[14:18]);
        ser.flushInput()
        ser.write(input_str.decode('hex'))
    else:
        print("Bad led's state vaule!")

def set_ntc_value(ntc_value):
    if judge_ntc_range(ntc_value) == True:
        input_str = mm_package("28", idx = ntc_value[0:2], module_id = None, pdata = ntc_value[2:6]);
        ser.flushInput()
        ser.write(input_str.decode('hex'))
    else:
        print("Bad ntc vaule!")

def get_result():
    input_str = mm_package("30", module_id = None);
    ser.flushInput()
    ser.write(input_str.decode('hex'))
    res = ser.readall()
    if res == "":
        print(error_message['serial_port'])
        return False
#NTC
    a = int(binascii.hexlify(res[6:8]), 16)
    print(int(binascii.hexlify(res[6:8]), 16))
    if (a < PMU_ADC['ntc_l']) or (a > PMU_ADC['ntc_h']):
        print(error_message['ntc_1'])
        return False
#VCC_INPUT
    a = int(binascii.hexlify(res[8:10]), 16)
    print(int(binascii.hexlify(res[8:10]), 16))
    if (a < PMU_ADC['v12_l']) or (a > PMU_ADC['v12_h']):
        print(error_message['v12'])
        return False
#VCORE1
    a = int(binascii.hexlify(res[10:12]), 16)
    print(int(binascii.hexlify(res[10:12]), 16))
    if (a < PMU_ADC['vcore_l']) or (a > PMU_ADC['vcore_h']):
        print(error_message['vcore_1'])
        return False
#VCORE2
    a = int(binascii.hexlify(res[12:14]), 16)
    print(int(binascii.hexlify(res[12:14]), 16))
    if (a < PMU_ADC['vcore_l']) or (a > PMU_ADC['vcore_h']):
        print(error_message['vcore_2'])
        return False
#VCORE3
    a = int(binascii.hexlify(res[14:16]), 16)
    print(int(binascii.hexlify(res[14:16]), 16))
    if (a < PMU_ADC['vcore_l']) or (a > PMU_ADC['vcore_h']):
        print(error_message['vcore_3'])
        return False
#PG1
    a = binascii.hexlify(res[16:18])
    print(int(binascii.hexlify(res[16:18]), 16))
    if (a != PMU_PG['pg_good']):
        print(error_message['pg_1'])
        return False
#PG2
    a = binascii.hexlify(res[18:20])
    print(int(binascii.hexlify(res[18:20]), 16))
    if (a != PMU_PG['pg_good']):
        print(error_message['pg_2'])
        return False
#PG3
    a = binascii.hexlify(res[20:22])
    print(int(binascii.hexlify(res[20:22]), 16))
    if (a != PMU_PG['pg_good']):
        print(error_message['pg_3'])
        return False
#LED1
    a = binascii.hexlify(res[22:24])
    print(int(binascii.hexlify(res[22:24]), 16))
    if (a != PMU_LED['led_close']):
        print(error_message['led_1'])
        return False
#LED2
    a = binascii.hexlify(res[24:26])
    print(int(binascii.hexlify(res[24:26]), 16))
    if (a != PMU_LED['led_close']):
        print(error_message['led_2'])
        return False
#LED3
    a = binascii.hexlify(res[26:28])
    print(int(binascii.hexlify(res[26:28]), 16))
    if (a != PMU_LED['led_close']):
        print(error_message['led_3'])
        return False
#NTC_MAX
    a = int(binascii.hexlify(res[28:30]), 16)
    print(int(binascii.hexlify(res[28:30]), 16))
    print(PMU_ADC['ntc_l'])
    print(PMU_ADC['ntc_h'])
    if (a < PMU_ADC['ntc_l']) or (a > PMU_ADC['ntc_h']):
        print(error_message['ntc_max'])
        return False
    return True

pmu_state_name = (
    'NTC:   ',
    'V12:    ',
    'VCORE1: ',
    'VCORE2: ',
    'VCORE3: ',
)

pmu_pg_state  = {
    '0001': 'Good',
    '0002': 'Bad'
}

pmu_led_state = {
    '0000': 'All Led Off',
    '0001': 'Green Led On',
    '0002': 'Red Led On',
    '0004': 'Green Led Blink',
    '0008': 'Red Led Blink'
}

def convert_to_vin(adc):
    return adc * 3.3 / 4095

def convert_to_vcore(vin):
    return vin / 20 * (20 + 43)

def convert_to_vcc(vin):
    return vin / 5.62 * (5.62 + 20)

SERIESRESISTOR=820
THERMISTORNOMINAL=10000
BCOEFFICIENT=3500
TEMPERATURENOMINAL=25
def convert_to_temp(adc):
    resistance = 4095 / adc - 1
    resistance = SERIESRESISTOR / resistance
    ret = resistance / THERMISTORNOMINAL
    ret = math.log(ret)
    ret /= BCOEFFICIENT
    ret += 1.0 / (TEMPERATURENOMINAL + 273.15)
    ret = 1.0 / ret
    ret -= 273.15

    return ret

def get_state():
    input_str = mm_package("30", module_id = None);
    ser.flushInput()
    ser.write(input_str.decode('hex'))
    res = ser.readall()
    if res == "":
        print (error_message['serial_port'])
        return False
#AD1~AD5
    for index in range(len(pmu_state_name)):
        a = int(binascii.hexlify(res[(index * 2 + 6):(index * 2 + 8)]), 16)
        if (index < 1):
            print(pmu_state_name[index] + '%d' %a + '(%f' %convert_to_temp(a) + 'C)')
        elif (index == 1):
            print(pmu_state_name[index] + '%d' %a + '(%f' %convert_to_vcc(convert_to_vin(a)) + 'V)')
        else:
            print(pmu_state_name[index] + '%d' %a + '(%f' %convert_to_vcore(convert_to_vin(a)) + 'V)')
#PG1~PG3
    a = binascii.hexlify(res[16:18])
    pmu_pg_state_key = pmu_pg_state.keys()
    for index in range(len(pmu_pg_state_key)):
        if a == pmu_pg_state_key[index]:
            print("PG1:    " + pmu_pg_state.get(pmu_pg_state_key[index]))
    a = binascii.hexlify(res[18:20])
    pmu_pg_state_key = pmu_pg_state.keys()
    for index in range(len(pmu_pg_state_key)):
        if a == pmu_pg_state_key[index]:
            print("PG2:    " + pmu_pg_state.get(pmu_pg_state_key[index]))
    a = binascii.hexlify(res[20:22])
    pmu_pg_state_key = pmu_pg_state.keys()
    for index in range(len(pmu_pg_state_key)):
        if a == pmu_pg_state_key[index]:
            print("PG3:    " + pmu_pg_state.get(pmu_pg_state_key[index]))
#LED1~LED3
    a = binascii.hexlify(res[22:24])
    pmu_led_state_key = pmu_led_state.keys()
    for index in range(len(pmu_led_state_key)):
        if a == pmu_led_state_key[index]:
            print("LED1:   " + pmu_led_state.get(pmu_led_state_key[index]))
    a = binascii.hexlify(res[24:26])
    pmu_led_state_key = pmu_led_state.keys()
    for index in range(len(pmu_led_state_key)):
        if a == pmu_led_state_key[index]:
            print("LED2:   " + pmu_led_state.get(pmu_led_state_key[index]))
    a = binascii.hexlify(res[26:28])
    pmu_led_state_key = pmu_led_state.keys()
    for index in range(len(pmu_led_state_key)):
        if a == pmu_led_state_key[index]:
            print("LED3:   " + pmu_led_state.get(pmu_led_state_key[index]))
#SET_NTC_MAX
    a = int(binascii.hexlify(res[28:30]), 16)
    print('NTC_MAX:    ' + '%d' %a + '(%f' %convert_to_temp(a) + 'C)')
    return True

def test_polling():
    while (True):
        h = raw_input("Please input(1-4), h for help:")
        if (h == 'h') or (h == 'H'):
            show_help()
        elif (h == 'q') or (h == 'Q'):
            sys.exit(0)
        elif h == '1':
            detect_version()
        elif h == '2':
            vol = raw_input("Please input the voltage:")
            set_vol_value(vol)
        elif h == '3':
            led = raw_input("Please input the led state:")
            set_led_state(led)
        elif h == '4':
            if (get_state() == False):
                sys.exit(0)
        else:
            show_help()

if __name__ == '__main__':
    while (True):
        if options.is_rig == '0':
            set_led_state("000000010000020000")
            set_vol_value("008008018008028008")
            set_ntc_value("00863d")
            if detect_version() == False:
                sys.exit(0)
            #Wait 3 seconds at least for power good
            time.sleep(3)
            if get_result() == False:
                set_led_state("000002010002020002")
                print(PMU_TYPE + " test fail")
            else:
                set_led_state("000001010001020001")
                print(PMU_TYPE + " test pass")
            set_vol_value("008008018008028008")
            raw_input("Please enter to continue:")
        elif options.is_rig == '1':
            test_polling()
        else:
            print("Input option wrong, please try again")
            sys.exit(0)
