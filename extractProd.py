import os, sys

def convert(ID):
    files = sorted(os.listdir('.'))
    dicoms = []
    for i in files:
        if i[:2] == ID:
            dicoms.append(i)
    dirnames = ['water', 'KO_1', 'KO_2', 'TO_1', 'TO_2', 'TI_1', 'TI_2', 'KI_1', 'KI_2']
    assert len(dicoms) == len(dirnames)
    output = open('extract.sh','w')
    for i in range(len(dicoms)):
        os.mkdir(dirnames[i])
        cmd = ['medcon', '-f', dicoms[i], '-c', 'png', '-o', dirnames[i]+'/'+dicoms[i]]
        print ' '.join(cmd)
        output.write(' '.join(cmd)+'\n')
    output.close()

if __name__ == '__main__':
    convert(sys.argv[1])
