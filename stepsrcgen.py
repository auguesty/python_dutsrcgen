from common import *

def onestepgen(tag35, tag10072, tag96):
    onestep_obj = STEP(tag35, tag10072, tag96)
    return onestep_obj



if __name__ == "__main__":
    print('hi')
    tag35 = b'UA3201'
    tag10072 = b'18823'
    tag96 = b'asd123123sad1231aasdasd'
    osp = onestepgen(tag35, tag10072, tag96)