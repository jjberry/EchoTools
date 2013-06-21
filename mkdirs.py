import os
import sys

def main(ID, txtfile): 
    files = sorted(os.listdir('.'))
    dicoms = []
    for i in files:
        if i[:2] == ID:
            dicoms.append(i)
    f = open(txtfile,'r').readlines()
    o = open('extract.sh','w')
    for i in range(len(f)):
        if f[i] != '\n':
            x = f[i][:-1].split('\t')
            name = '%02d_%s_%s' % (int(x[0]), x[2][:-4], dicoms[i][-2:])
            os.mkdir(name)
            cmd = ['medcon', '-f', dicoms[i], '-c', 'png', '-o', name+'/'+dicoms[i]]
            print ' '.join(cmd)
            o.write(' '.join(cmd)+'\n')
    o.close()
        

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

