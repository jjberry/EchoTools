import os

files = sorted(os.listdir('.'))
dicoms = []
for i in files:
    if i[:2] == '2X':
        dicoms.append(i)
f = open('conditions.txt','r').readlines()
o = open('extract.sh','w')
for i in range(len(f)):
    if f[i] != '\n':
        x = f[i][:-1].split('\t')
        name = '%02d_%s_%s' % (int(x[0]), x[2][:-4], dicoms[i/2][-2:])
        os.mkdir(name)
        cmd = ['"/c/Program Files/XMedCon/bin/medcon.exe"', '-f', dicoms[i/2], '-c', 'png', '-o', name+'/'+dicoms[i/2]]
        print ' '.join(cmd)
        o.write(' '.join(cmd)+'\n')
o.close()
        
