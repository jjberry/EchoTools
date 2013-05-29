'''
Created on May 29, 2013

Conversion from RGB to HSV colorspace

@author: Jeff
'''
import Image
import numpy as np 

def RGB2HSV(filename):
    i = Image.open(filename).convert('RGB')
    a = np.asarray(i, int)

    R, G, B = a.T

    m = np.min(a,2).T
    M = np.max(a,2).T
    
    C = M-m #chroma
    Cmsk = C!=0
    
    #Hue
    H = np.zeros(R.shape, int)
    mask = (M==R)&Cmsk
    H[mask] = np.mod(60*(G-B)/C, 360)[mask]
    mask = (M==G)&Cmsk
    H[mask] = (60*(B-R)/C + 120)[mask]
    mask = (M==B)&Cmsk
    H[mask] = (60*(R-G)/C + 240)[mask]
    H *= 180 #this controls the range of H
    H /= 360
    
    #Value
    V = M

    #Saturation
    S = np.zeros(R.shape, int)
    S[Cmsk] = ((255*C)/V)[Cmsk]

    return H.T
