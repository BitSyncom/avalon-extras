#!/usr/bin/env python2.7

# This simple script was for test A3212 modular.
# There are ? cores in one A3212 chip.
# If all cores are working the core num should display.
# If some of them not working, it will display 'X'.
# Depends : PyUSB 1.0 (Under Linux)
# PyUSB 1.0 Installation: https://github.com/walac/pyusb
#
#  bridge format: length[1]+transId[1]+sesId[1]+req[1]+data[60]
#  length: 4+len(data)
#  transId: 0
#  sesId: 0
#  req:
#        a0:RESET
#        a1:INIT
#        a2:DEINIT
#        a3:WRITE
#        a4:READ
#        a5:XFER
#        a6:XFER
#  data: the actual payload
#        clockRate[4] + reserved[4] + payload[52] when init
#
#        xparam[4] + payload[56] when write
#            xparam: txSz[1]+rxSz[1]+options[1]+slaveAddr[1]
#
#        payload[60] when read
#
from optparse import OptionParser
import binascii
import usb.core
import usb.util
import sys

parser = OptionParser(version="%prog ver:20160808_1649")
# TODO: Add test core count
parser.add_option("-C", "--core", dest="test_cores",
                  default="4", help="Test cores")
parser.add_option("-F", "--freq", dest="freq", default="200",
                  help="Asic freq, default:200")
(options, args) = parser.parse_args()
parser.print_version()

auc_vid = 0x29f1
auc_pid = 0x33f2


def CRC16(message):
    # CRC-16-CITT poly, the CRC sheme used by ymodem protocol
    poly = 0x1021
    # 16bit operation register, initialized to zeros
    reg = 0x0000
    # pad the end of the message with the size of the poly
    message += '\x00\x00'
    # for each bit in the message
    for byte in message:
        mask = 0x80
        while(mask > 0):
            # left shift by one
            reg <<= 1
            # input the next bit from the message into the right hand side
            # of the op reg
            if ord(byte) & mask:
                reg += 1
            mask >>= 1
            # if a one popped out the left of the reg, xor reg w/poly
            if reg > 0xffff:
                # eliminate any one that popped out the left
                reg &= 0xffff
            # xor with the poly, this is the remainder
                reg ^= poly
    return reg


def enum_usbdev(vendor_id, product_id):
    # Find device
    usbdev = usb.core.find(idVendor=vendor_id, idProduct=product_id)

    if not usbdev:
        return None, None, None

    try:
        # usbdev[iConfiguration][(bInterfaceNumber,bAlternateSetting)]
        for endp in usbdev[0][(1, 0)]:
            if endp.bEndpointAddress & 0x80:
                endpin = endp.bEndpointAddress
            else:
                endpout = endp.bEndpointAddress

    except usb.core.USBError as e:
        sys.exit("Could not set configuration: %s" % str(e))

    return usbdev, endpin, endpout

# addr : iic slaveaddr
# req : see bridge format
# data: 40 bytes payload


def auc_req(usbdev, endpin, endpout, addr, req, data):
    req = req.rjust(2, '0')

    if req == 'a1':
        data = data.ljust(120, '0')
        datalen = 12
        txdat = hex(datalen)[2:].rjust(2, '0') + "0000" + req + data
        usbdev.write(endpout, txdat.decode("hex"))

    # FIXME: a3 not work
    if req == 'a3':
        datalen = 8 + (len(data) / 2)
        data = data.ljust(112, '0')
        txdat = hex(datalen)[2:].rjust(2, '0') + "0000" + \
            "a5" + "280000" + addr.rjust(2, '0') + data
        usbdev.write(endpout, txdat.decode("hex"))
        usbdev.read(endpin, 64)

    # FIXME: a4 not work
    if req == 'a4':
        datalen = 8
        txdat = hex(datalen)[2:].rjust(2, '0') + "0000" + "a5" + \
            "002800" + addr.rjust(2, '0') + "0".ljust(112, '0')
        usbdev.write(endpout, txdat.decode("hex"))

    if req == 'a5':
        if options.fast_xfer == '1':
            datalen = 8 + (len(data) / 2)
            data = data.ljust(112, '0')
            txdat = hex(datalen)[2:].rjust(2, '0') + "0000" + \
                "a5" + "282800" + addr.rjust(2, '0') + data
            usbdev.write(endpout, txdat.decode("hex"))
        else:
            datalen = 8 + (len(data) / 2)
            data = data.ljust(112, '0')
            txdat = hex(datalen)[2:].rjust(2, '0') + "0000" + \
                "a5" + "280000" + addr.rjust(2, '0') + data
            usbdev.write(endpout, txdat.decode("hex"))
            usbdev.read(endpin, 64)

            datalen = 8
            txdat = hex(datalen)[2:].rjust(
                2, '0') + "0000" + "a5" + "002800" + addr.rjust(2, '0') + "0".ljust(112, '0')
            usbdev.write(endpout, txdat.decode("hex"))

    if req == 'a6':
        datalen = 4
        txdat = hex(datalen)[2:].rjust(2, '0') + "0000" + req
        usbdev.write(endpout, txdat.decode("hex"))


def auc_read(usbdev, endpin):
    ret = usbdev.read(endpin, 64)
    if ret[0] > 4:
        return ret[4:ret[0]]
    else:
        return None


def auc_xfer(usbdev, endpin, endpout, addr, req, data):
    auc_req(usbdev, endpin, endpout, addr, req, data)
    return auc_read(usbdev, endpin)

TYPE_TEST = "32"


def mm_package(cmd_type, idx="00", cnt="01", module_id=None, pdata='0'):
    if module_id is None:
        data = pdata.ljust(64, '0')
    else:
        data = pdata.ljust(60, '0') + module_id.rjust(4, '0')

    crc = CRC16(data.decode("hex"))
    idx += 1
    return "434e" + cmd_type + "00" + idx + cnt + data + hex(crc)[2:].rjust(4, '0')

errcode = [
        'IDLE',
        '\x1b[1;31mMMCRCFALIED\x1b[0m',
        '\x1b[1;31mNOFAN\x1b[0m',
        '\x1b[1;31mLOCK\x1b[0m',
        '\x1b[1;31mAPIFIF00VERFLOW\x1b[0m',
        'RBOVERFLOW',
        'TOOHOT',
        '\x1b[1;31mHOTBEFORE\x1b[0m',
        '\x1b[1;31mLOOPFAILD\x1b[0m',
        '\x1b[1;31mCORETESTFAILED\x1b[0m',
        '\x1b[1;31mINVALIDMCU\x1b[0m',
        '\x1b[1;31mPGFAILD\x1b[0m',
        '\x1b[1;31mNTC_ERR\x1b[0m',
        '\x1b[1;31mVOL_ERR\x1b[0m',
        '\x1b[1;31mVCORE_ERR\x1b[0m'
        ]


def run_testa7(usbdev, endpin, endpout, cmd):
    count = 0
    passcore = 0
    while True:
        auc_req(usbdev, endpin, endpout, "00", "a3", cmd)

        while True:
            auc_req(usbdev, endpin, endpout,
                    "00",
                    "a4",
                    cmd)
            res_s = auc_read(usbdev, endpin)
            if res_s is not None:
                break

        if not res_s:
            print("Something is wrong or modular id not correct")
        else:
            result = binascii.hexlify(res_s)
            print result
            count = count + 1
            nhu = int(result[10: 12], 16)
            ncore = int(result[16: 20], 16)
            num_hu = int(result[8: 10], 16)
            passcore = int(result[12: 16], 16) + passcore
            sys.stdout.write("M-" + str(num_hu) + ': ')
            if (ncore % 8) == 0:
                c = result[40: (ncore / 8) * 2 + 40]
                n = int(c, 16)
                r = ''
                cnt = 0
                for j in range(ncore, 0, -8):
                    for cnt in range(7, -1, -1):
                        if ((n >> cnt) & 1) == 0:
                            r = '\x1b[1;31mxx\x1b[0m {}'.format(r)
                        else:
                            r = '\x1b[1;32m{:02d}\x1b[0m {}'.format(
                                j + cnt - 7, r)

                    n >>= 8
                print(r)
            else:
                c = result[40: (ncore / 8 + 1) * 2 + 40]
                n = int(c, 16)
                r = ''
                cnt = 0
                for j in range(ncore, 0, -8):
                    if j == ncore:
                        for cnt in range(ncore - ncore / 8 * 8 - 1, -1, -1):
                            if ((n >> cnt) & 1) == 0:
                                r = '\x1b[1;31mxx\x1b[0m {}'.format(r)
                            else:
                                r = '\x1b[1;32m{:02d}\x1b[0m {}'.format(
                                    j + cnt - ncore / 8 * 8 - 1, r)
                    else:
                        for cnt in range(7, -1, -1):
                            if ((n >> cnt) & 1) == 0:
                                r = '\x1b[1;31mxx\x1b[0m {}'.format(r)
                            else:
                                r = '\x1b[1;32m{:02d}\x1b[0m {}'.format(
                                    j + cnt - ncore / 8 * 8 - 1, r)

                    n >>= 8
                print(r)
        if count == nhu:
            break
    allcore = int(result[16: 20], 16) * nhu
    ec = int(result[24:32], 16)
    display = 'bad(' + str(int(allcore) - passcore) + '), '
    display = display + 'all(' + str(allcore) + '), '
    errstr = ''
    for i in range(0, len(errcode)):
        if ((ec >> i) & 1):
            errstr += errcode[i] + ' '

    display = display + 'Status ( ' + errstr + ')'
    print('Result:' + display)
    raw_input("Please enter any key to continue")

if __name__ == '__main__':
    # Detect AUC
    usbdev, endpin, endpout = enum_usbdev(auc_vid, auc_pid)
    if usbdev:
        ret = auc_xfer(usbdev, endpin, endpout, "00", "a1", "801A0600")
        if ret:
            print "AUC ver: " + ''.join([chr(x) for x in ret])
        else:
            print "AUC ver null"

    if usbdev is None:
        print "No Avalon USB Converter or compatible device can be found!"
        sys.exit("Enum failed!")
    else:
        print "Find an Avalon USB Converter or compatible device"

    freqdata = {}
    tmp = options.freq.split(",")
    if len(tmp) == 0:
        freqdata[0] = 200
        freqdata[1] = freqdata[2] = 200
    if len(tmp) == 1:
        freqdata[2] = freqdata[1] = freqdata[0] = tmp[0]
    if len(tmp) == 2:
        freqdata[0] = tmp[0]
        freqdata[2] = freqdata[1] = tmp[1]
    if len(tmp) == 3:
        freqdata[0] = tmp[0]
        freqdata[1] = tmp[1]
        freqdata[2] = tmp[2]

    tmp = hex(int(options.test_cores, 10))[2:]
    txdata = tmp.rjust(8, '0')
    tmp = tmp.rjust(8, '0')
    txdata += tmp
    tmp = hex(int(freqdata[0], 10) | (int(freqdata[1], 10) << 10) | (
        int(freqdata[2], 10) << 20))[2:]
    tmp = tmp.rjust(8, '0')
    txdata += tmp
    run_testa7(usbdev, endpin, endpout, mm_package(TYPE_TEST, pdata=txdata))