from collections import OrderedDict
from datetime import datetime
import random, csv, binascii, math
import template

# ================================================================================ parameter
steptype_tuple = (
    b'UA5801',
    b'UA3201',
    b'UA3202',
    b'UA3113',
    b'UA3802',
    b'UA3901',
    b'UA9002',
    b'UA3115'
)


def tplist2dict(template_list):
    tp_dict = OrderedDict()
    for tag in template_list:
        tp_dict[tag[0]] = tag[1:]
    return tp_dict


tpdict = dict()
tpdict[3113] = tplist2dict(template.template_3113)
tpdict[3201] = tplist2dict(template.template_3201)
tpdict[3202] = tplist2dict(template.template_3202)
tpdict[3802] = tplist2dict(template.template_3802)
tpdict[3901] = tplist2dict(template.template_3901)
tpdict[5801] = tplist2dict(template.template_5801)
tpdict[9002] = tplist2dict(template.template_9002)

intrange_dict = {
    'int32': (-0x7fff_ffff, 0x7fff_ffff),
    'uint32': (0, 0xffff_ffff),
    'int64': (-0x7fff_ffff_ffff_ffff, 0x7fff_ffff_ffff_ffff),
    'uint64': (0, 0xffff_ffff_ffff_ffff)
}


# ================================================================================ function
def gettag10142_fromtag35(tag35: bytes) -> bytes:
    if tag35 == b'UA3108':
        tag10142 = b'56'
    elif tag35 == b'UA3209':
        tag10142 = b'57'
    elif tag35 == b'UA5801':
        tag10142 = b'58'
    elif tag35 == b'UA3201':
        tag10142 = b'7'
    elif tag35 == b'UA3202' or tag35 == b'UA3113' or tag35 == b'UA3115':
        tag10142 = b'6'
    elif tag35 == b'UA3802':
        tag10142 = b'38'
    elif tag35 == b'UA3901':
        tag10142 = b'39'
    elif tag35 == b'UA9002':
        tag10142 = b'40'
    else:
        tag10142 = b'A'
    return tag10142


def enc_string(csvdata: str) -> bytes:
    hextmp_l = csvdata[:-1].encode().hex()
    hextmp_r = csvdata[-1].encode().hex()
    hextmp_r = int(hextmp_r, 16) | 0x80
    hextmp_r = hex(hextmp_r)[2:]
    hextmp = hextmp_l + hextmp_r
    bytestmp = binascii.a2b_hex(hextmp)
    return bytestmp


def enc_int32(require: bool, csvdata: str):
    # csvdata range detect
    csvdata_int = int(csvdata, 10)
    if not intrange_dict["int32"][0] <= csvdata_int <= intrange_dict["int32"][1]:
        raise RuntimeError(f'{"int32":s} no in range {str(intrange_dict["int32"]):s}')
    # optional and >= 0, +1
    if not require and csvdata_int >= 0:
        csvdata_int += 1
    # get bin
    if csvdata_int < 0:
        sig = '1'
        tmp0_int = csvdata_int * -1
        tmp0_bin = bin(tmp0_int)[2:]
        tmp1_bin = ''
        for i in tmp0_bin:
            if i == '0':
                tmp1_bin += '1'
            else:
                tmp1_bin += '0'
        tmp2_bin = tmp1_bin
    else:
        sig = '0'
        tmp1_bin = bin(csvdata_int)
        tmp2_bin = tmp1_bin[2:]
    tmp2_bin_1blen = 1 + len(tmp2_bin)
    tmp2_bin_7blen = math.ceil(tmp2_bin_1blen / 7.0)
    tmp2_bin_1blenfill = (tmp2_bin_7blen)*7
    tmp2_hex = hex(int(tmp2_bin, 2))[2:]
    # fill 7b
    tmp3_bin = (tmp2_bin_1blenfill - tmp2_bin_1blen) * sig + tmp2_bin
    tmp3_bin_len = len(tmp3_bin)
    tmp4_bin7b_list = [tmp3_bin[i*7:i*7+7] for i in range(tmp2_bin_7blen)]
    # 7b -> 8b
    tmp5_bin8b_list = list()
    for index in range(len(tmp4_bin7b_list)):
        if index == len(tmp4_bin7b_list) - 1:
            tmp5_bin8b_list.append('1'+tmp4_bin7b_list[index])
        else:
            tmp5_bin8b_list.append('0'+tmp4_bin7b_list[index])
    tmp6_hex1B_list = [hex(int(i, 2))[2:] for i in tmp5_bin8b_list]
    tmp7_hex = ''.join(tmp6_hex1B_list)
    tmp8_bytes = tmp7_hex.encode()
    return tmp8_bytes




# ================================================================================ class
# generate step pkg(8=STEP.1.0.0 ...... .10=xxx.)
class STEP(object):
    def __init__(self, tag35: bytes, tag10072: bytes, tag96: bytes):
        self.tag35 = tag35
        self.tag10072 = tag10072
        self.tag95 = str(len(tag96)).encode()
        self.tag96 = tag96
        self.__onestepgen__()

    def __onestepgen__(self):
        # init
        stepdict = OrderedDict()

        # modify by order
        stepdict[b'8'] = b'STEP.1.0.0'
        stepdict[b'9'] = None
        stepdict[b'35'] = self.tag35
        stepdict[b'49'] = b'VDE'
        stepdict[b'56'] = b'VSS'
        stepdict[b'34'] = b'0'
        stepdict[b'52'] = datetime.now().strftime("%Y%m%d-%H:%M:%S").encode()
        stepdict[b'10142'] = gettag10142_fromtag35(self.tag35)
        stepdict[b'10072'] = self.tag10072
        stepdict[b'50'] = b'1'
        stepdict[b'95'] = self.tag95
        stepdict[b'96'] = self.tag96
        stepdict[b'10'] = b'ABC'  # need rectify later

        # modify tag9 and tag10
        totallen = 0
        for tag in stepdict.keys():
            if tag not in [b'8', b'9', b'10', ]:
                totallen += len(tag) + 1 + len(stepdict[tag]) + 1  # tag=value<SOH>
        stepdict[b'9'] = str(totallen).encode()

        self.stepdict = stepdict
        self.stepbytes = bytes()
        for tag in stepdict.keys():
            self.stepbytes += tag + b'=' + stepdict[tag] + b'\x01'


# generate fix pkg(8=FIX ...... .10=xxx.)
class FIX(object):
    tag34 = 0

    def __init__(self, tag35: bytes, tag96: bytes):
        self.tag35 = tag35
        FIX.tag34 += 1
        self.tag34 = str(FIX.tag34).encode()
        self.tag95 = str(len(tag96)).encode()
        self.tag96 = tag96
        self.__onefixgen__()

    def __onefixgen__(self):
        # init
        fixdict = OrderedDict()

        # modify by order
        fixdict[b'8'] = b'FIXT.1.1'
        fixdict[b'9'] = None
        fixdict[b'35'] = self.tag35
        fixdict[b'49'] = b'EzEI.1.1'
        fixdict[b'56'] = b'EzSR.2010600'
        fixdict[b'34'] = self.tag34
        fixdict[b'52'] = datetime.now().strftime("%Y%m%d-%H:%M:%S").encode()[:21]
        fixdict[b'347'] = b'GBK'
        fixdict[b'167'] = b'02'
        fixdict[b'339'] = b'3'
        if self.tag35 == b'W':
            fixdict[b'1180'] = b'47831'
            fixdict[b'1181'] = b'28646'
            fixdict[b'75'] = datetime.now().strftime("%Y%m%d").encode()
            fixdict[b'779'] = datetime.now().strftime("%H%M%S%f").encode()[:8]
            fixdict[b'265'] = b'111'
            fixdict[b'5468'] = b'5'
            fixdict[b'95'] = self.tag95
            fixdict[b'96'] = self.tag96
        else:
            fixdict[b'336'] = b'T00'
            fixdict[b'393'] = b'204'
        fixdict[b'10'] = b'ABC'  # need rectify later

        # modify tag9 and tag10
        totallen = 0
        for tag in fixdict.keys():
            if tag not in [b'8', b'9', b'10', ]:
                totallen += len(tag) + 1 + len(fixdict[tag]) + 1  # tag=value<SOH>
        fixdict[b'9'] = str(totallen).encode()

        self.fixdict = fixdict
        self.fixbytes = bytes()
        for tag in fixdict.keys():
            self.fixbytes += tag + b'=' + fixdict[tag] + b'\x01'


# generate tag96 value
class PREFETCH(object):
    def __init__(self, rd, rdlen=None, prefetchbytes=None):
        """
        :param rd: random choice, True/False
        :param rdlen: int
        :param data: bytes
        """
        if rd:
            self.prefetchbytes = random.randbytes(rdlen)
        else:
            self.prefetchbytes = prefetchbytes


# split fast dicts(before encode) into step dict by tag10072
class CSVSPLIT(object):
    def __init__(self, csvfile):
        order_csv = open(csvfile, newline='')
        self.order_reader = csv.DictReader(order_csv)
        self.__split__()
        order_csv.close()

    def __split__(self):
        stepsplit_dict = OrderedDict()
        for srcfastdict in self.order_reader:
            if srcfastdict['10072'] not in stepsplit_dict.keys():
                stepsplit_dict[srcfastdict['10072']] = list()
            stepsplit_dict[srcfastdict['10072']].append(OrderedDict(srcfastdict))
        self.stepsplit_dict = stepsplit_dict


class GETTAG(object):
    def __init__(self, tp, csvdata, predict):
        self.tp = tp
        self.require = tp[0]
        self.op = tp[1]
        self.dtype = tp[2]
        self.outshow = tp[3]
        self.csvdata = csvdata

        if self.op == 'default':
            if self.dtype == 'string':
                if not self.require:
                    if self.csvdata == 'Null':
                        self.encdata = '80'
                        self.pmapbit = 1
                    elif self.csvdata == '':
                        self.encdata = '0080'
                        self.pmapbit = 1
                    elif self.csvdata == 'default':
                        self.encdata = None
                        self.pmapbit = 0
                    else:
                        self.encdata = enc_string(self.csvdata)
                        self.pmapbit = 1
                else:
                    if self.csvdata == 'Null':
                        raise RuntimeError('default, string, 必要, 不可Null')
                    elif self.csvdata == '':
                        self.encdata = '80'
                        self.pmapbit = 1
                    elif self.csvdata == 'default':
                        raise RuntimeError('default, string, 必要, 暂不支持default类型输入')
                    else:
                        # self.encdata = self.csvdata.encode().hex()
                        self.encdata = enc_string(self.csvdata)
                        self.pmapbit = 1

            elif self.dtype == 'int32':
                if not self.require:
                    if self.csvdata == 'Null':
                        self.encdata = '80'
                        self.pmapbit = 1
                    elif self.csvdata == '0':
                        self.encdata = '81'
                        self.pmapbit = 1
                    elif self.csvdata == '':
                        raise RuntimeError("default, int32, optional, cannot mate with ''")
                    elif self.csvdata == 'default':
                        self.encdata = None
                        self.pmapbit = 0
                    else:
                        pass



                else:
                    pass


            elif self.dtype == 'int64':
                pass
            elif self.dtype == 'uint32':
                pass
            elif self.dtype == 'uint64':
                pass
            else:
                raise RuntimeError('wrong dtype')
        elif self.op == 'copy':
            pass
        elif self.op == 'increment':
            pass
        elif self.op == 'none':
            pass
        elif self.op == 'constant':
            pass
        else:
            raise RuntimeError('wrong or unsupported op')


# encode 3201 fasts in one step
class ENCODE3201(object):
    PREDICT = dict()

    def __init__(self, srcfasts_list):
        self.template = tpdict[3201]
        self.srcfasts_list = srcfasts_list
        self.__encode_many__()

    def __encode_many__(self):
        encfastdict = OrderedDict()
        for srcfastdict in self.srcfasts_list:
            for tag in srcfastdict.keys():
                if tag in ['10072', '35', ]:
                    pass
                elif tag == '999':  # ('Y', 'copy', 'int32', False, 'nrepeat')
                    csvdata = srcfastdict['999']
                    tp = self.template['00999']
                    gt = GETTAG(tp, csvdata, ENCODE3201.PREDICT)


if __name__ == "__main__":
    enc_string('600613')
    enc_int32(False, '942755')
    enc_int32(True, '942755')
    enc_int32(False, '-942755')
    enc_int32(True, '-7942755')
    tp3201_dict = tplist2dict(template.template_3201)
    mo3201 = CSVSPLIT("./order3201.csv")
    for srcfasts_list in mo3201.stepsplit_dict.values():
        o3201 = ENCODE3201(srcfasts_list)
        print('debug')