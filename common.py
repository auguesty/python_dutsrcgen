from collections import OrderedDict
from datetime import datetime
import random
import csv
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
        for fastdict in self.order_reader:
            if fastdict['10072'] not in stepsplit_dict.keys():
                stepsplit_dict[fastdict['10072']] = list()
            stepsplit_dict[fastdict['10072']].append(fastdict)
        self.stepsplit_dict = stepsplit_dict


"""
fast encode rule----
default     :
copy        :
increment   :
none        :
"""

# encode 3201 fasts in one step
class ENCODE3201(object):
    def __init__(self, fasts_list):
        self.fasts_list = fasts_list








if __name__ == "__main__":
    tp3201_dict = tplist2dict(template.template_3201)
    mo3201 = CSVSPLIT("./order3201.csv")
    for fasts_list in mo3201.stepsplit_dict.values():
        o3201 = ENCODE3201(fasts_list)
        print('debug')