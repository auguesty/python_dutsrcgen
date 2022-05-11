from common import *

def case1(rdlen):
    pf1_obj = PREFETCH(rd=True, rdlen=rdlen)
    step_obj = STEP(tag35=b'UA3201', tag10072=b'1', tag96=pf1_obj.prefetchbytes)
    return step_obj.stepbytes

def case2():
    tmp_list = list()
    for i in range(1_0000, 2_0000, 342):
        tmp_list.append(case1(i))
    return tmp_list


if __name__ == "__main__":
    import os
    runpath = os.path.abspath('')
    srcpath = os.path.join(runpath, 'src')
    if not os.path.exists(srcpath):
        os.mkdir(srcpath)
    stepsrc_file = os.path.join(srcpath, "stepsrc.dat")
    f = open(stepsrc_file, "wb+")

    t2 = case2()
    for i in t2:
        f.write(i)
    f.close()
    print('done')