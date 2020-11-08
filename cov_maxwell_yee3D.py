#
# author:         L. Pezzini
# e-mail :        luca.pezzini@edu.unito.it
# date:           28.10.2020
# copyright:      2020 KU Leuven (c)
# MIT license
#

#
# Maxwell Solver 3D
#       • General coordinates
#       • Energy conserving
#       • Mimetic operator
#

import numpy as np
import matplotlib.pyplot as plt
import time
import math
import sys

# Time steps
Nt = 500 
dt = 0.001
# Nodes
Nx1 = 100
Nx2 = 100
Nx3 = 1

# Computational domain 
x1min, x1max = 0, 1    
x2min, x2max = 0, 1    
x3min, x3max = 0, .25  
Lx1 = int(abs(x1max - x1min))
Lx2 = int(abs(x2max - x2min)) 
Lx3 = abs(x2max - x2min)
dx1 = Lx1/Nx1 
dx2 = Lx2/Nx2
dx3 = Lx3/Nx3

# Geometry: Tensor and Jacobian
J = np.ones([Nx1, Nx2, Nx3], dtype=float) 
gx1x1 = np.ones([Nx1, Nx2, Nx3], dtype=float)
gx1x2 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
gx1x3 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
gx2x1 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
gx2x2 = np.ones([Nx1, Nx2, Nx3], dtype=float)
gx2x3 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
gx3x1 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
gx3x2 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
gx3x3 = np.ones([Nx1, Nx2, Nx3], dtype=float)
# Grid matrix
x1 = np.linspace(x1min, Lx1 - dx1, Nx1, dtype=float)
x2 = np.linspace(x2min, Lx2 - dx2, Nx2, dtype=float)
x3 = np.linspace(x3min, Lx3 - dx3, Nx3, dtype=float)
x1v, x2v, x3v = np.meshgrid(x1, x2, x3, indexing='ij')
# Field matrix
Ex1 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
Ex2 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
Ex3 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
Bx1 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
Bx2 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
Bx3 = np.zeros([Nx1, Nx2, Nx3], dtype=float) 
# Field matrix (old)
Ex1_old = np.zeros([Nx1, Nx2, Nx3], dtype=float)
Ex2_old = np.zeros([Nx1, Nx2, Nx3], dtype=float)
Ex3_old = np.zeros([Nx1, Nx2, Nx3], dtype=float)
Bx1_old = np.zeros([Nx1, Nx2, Nx3], dtype=float)
Bx2_old = np.zeros([Nx1, Nx2, Nx3], dtype=float)
Bx3_old = np.zeros([Nx1, Nx2, Nx3], dtype=float)
# Curl of fields
curl_Ex1 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
curl_Ex2 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
curl_Ex3 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
curl_Bx1 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
curl_Bx2 = np.zeros([Nx1, Nx2, Nx3], dtype=float)
curl_Bx3 = np.zeros([Nx1, Nx2, Nx3], dtype=float)

#Perturbation
Bx3[int((Nx1-1)/2), int((Nx2-1)/2), :] = 1.
# Total energy
U = np.zeros(Nt, dtype=float) 
# Divergence of E
divB = np.zeros(Nt, dtype=float) 

# Grid begin & end point
# Note we don't start from 0 cause 0 and Nx1-1 are the same node
ib = 1
ie = Nx1 - 1
jb = 1
je = Nx1 - 1
kb = 1
ke = Nx1 - 1


def myplot(values, name):
    plt.figure(name)
    plt.imshow(values.T, origin='lower', extent=[0, Lx1, 0, Lx2], aspect='equal', vmin=-0.1, vmax=0.1, cmap='plasma')
    plt.colorbar()

def myplot2(values, name):
    plt.figure(name)
    plt.plot(values)


def curl(Ax1, Ax2, Ax3, field):   
    # Fieldtype = 0 -> B field
    # Fieldtype = 1 -> E field
    if field == 0:
        curl_x1 = (gx3x1[ib+1:ie+1, jb:je, kb:ke]*Ax1[ib+1:ie+1, jb:je, kb:ke]        - gx3x1[ib+1:ie+1, jb-1:je-1, kb:ke]*Ax1[ib+1:ie+1, jb-1:je-1, kb:ke]\
        +         gx3x1[ib:ie, jb:je, kb:ke]*Ax1[ib:ie, jb:je, kb:ke]                 - gx3x1[ib:ie, jb-1:je-1, kb:ke]*Ax1[ib:ie, jb-1:je-1, kb:ke]\
        +         gx3x2[ib:ie, jb+1:ie+1, kb:ke]*Ax2[ib:ie, jb+1:je+1, kb:ke]         - gx3x2[ib:ie, jb-1:je-1, kb:ke]*Ax2[ib:ie, jb-1:je-1, kb:ke]\
        +     2.*(gx3x3[ib:ie, jb:je, kb:ke]*Ax3[ib:ie, jb:je, kb:ke]                 - gx3x3[ib:ie, jb-1:je-1, kb:ke]*Ax3[ib:ie, jb-1:je-1, kb:ke]))/(2.*dx2*J[ib:ie, jb:je, kb:ke])\
        -        (gx2x1[ib+1:ie+1, jb:je, kb:ke]*Ax1[ib+1:ie+1, jb:je, kb:ke]         - gx2x1[ib+1:ie+1, jb:je, kb-1:ke-1]*Ax1[ib+1:ie+1, jb:je, kb-1:ke-1]\
        +         gx2x1[ib:ie, jb:je, kb:ke]*Ax1[ib:ie, jb:je, kb:ke]                 - gx2x1[ib:ie, jb:je, kb-1:ke-1]*Ax1[ib:ie, jb:je, kb-1:ke-1]\
        +     2.*(gx2x2[ib:ie, jb:je, kb:ke]*Ax2[ib:ie, jb:je, kb:ke]                 - gx2x2[ib:ie, jb:je, kb-1:ke-1]*Ax2[ib:ie, jb:je, kb-1:ke-1])\
        +         gx2x3[ib:ie, jb:je, kb+1:ke+1]*Ax3[ib:ie, jb:je, kb+1:ke+1]         - gx2x3[ib:ie, jb:je, kb-1:ke-1]*Ax3[ib:ie, jb:je, kb-1:ke-1])/(2.*dx3*J[ib:ie, jb:je, kb:ke])
        curl_x2 = (2.*(gx1x1[ib:ie, jb:je, kb:ke]*Ax1[ib:ie, jb:je, kb:ke]            - gx1x1[ib:ie, jb:je, kb-1:ke-1]*Ax1[ib:ie, jb:je, kb-1:ke-1])\
        +         gx1x2[ib:ie, jb+1:je+1, kb:ke]*Ax2[ib:ie, jb+1:je+1, kb:ke]         - gx1x2[ib:ie, jb+1:je+1, kb-1:ke-1]*Ax2[ib:ie, jb+1:je+1, kb-1:ke-1]\
        +         gx1x2[ib:ie, jb:je, kb:ke]*Ax2[ib:ie, jb:je, kb:ke]                 - gx1x2[ib:ie, jb:je, kb-1:ke-1]*Ax2[ib:ie, jb:je, kb-1:ke-1]\
        +         gx1x3[ib:ie, jb:je, kb+1:ke+1]*Ax3[ib:ie, jb:je, kb+1:ke+1]         - gx1x3[ib:ie, jb:je, kb-1:ke-1]*Ax3[ib:ie, jb:je, kb-1:ke-1])/(2.*dx3*J[ib:ie, jb:je, kb:ke])\
        -        (gx3x1[ib+1:ie+1, jb:je, kb:ke]*Ax1[ib+1:ie+1, jb:je, kb:ke]         - gx3x1[ib-1:ie-1, jb:je, kb:ke]*Ax1[ib-1:ie-1, jb:je, kb:ke]\
        +         gx3x2[ib:ie, jb+1:je+1, kb:ke]*Ax2[ib:ie, jb+1:je+1, kb:ke]         - gx3x2[ib-1:ie-1, jb+1:je+1, kb:ke]*Ax2[ib-1:ie-1, jb+1:je+1, kb:ke]\
        +         gx3x2[ib:ie, jb:je, kb:ke]*Ax2[ib:ie, jb:je, kb:ke]                 - gx3x2[ib-1:ie-1, jb:je, kb:ke]*Ax2[ib-1:ie-1, jb:je, kb:ke]\
        +     2.*(gx3x3[ib:ie, jb:je, kb:ke]*Ax3[ib:ie, jb:je, kb:ke]                 - gx3x3[ib-1:ie-1, jb:je, kb:ke]*Ax3[ib-1:ie-1, jb:je, kb:ke]))/(2.*dx1*J[ib:ie, jb:je, kb:ke])
        curl_x3 = (gx2x1[ib+1:ie+1, jb:je, kb:ke]*Ax1[ib+1:ie+1, jb:je, kb:ke]        - gx2x1[ib-1:ie-1, jb:je, ib:ke]*Ax1[ib-1:ie-1, jb:je, kb:ke]\
        +     2.*(gx2x2[ib:ie, jb:je, kb:ke]*Ax2[ib:ie, jb:je, kb:ke]                 - gx2x2[ib-1:ie-1, jb:je, kb:ke]*Ax2[ib-1:ie-1, jb:je, kb:ke])\
        +         gx2x3[ib:ie, jb:je, kb+1:ke+1]*Ax3[ib:ie, jb:je, kb+1:ke+1]         - gx2x3[ib-1:ie-1, jb:je, kb+1:ke+1]*Ax3[ib-1:ie-1, jb:je, kb+1:ke+1]\
        +         gx2x3[ib:ie, jb:je, kb:ke]*Ax3[ib:ie, jb:je, kb:ke]                 - gx2x3[ib-1:ie-1, jb:je, kb:ke]*Ax3[ib-1:ie-1, jb:je, kb:ke])/(2.*dx1*J[ib:ie, jb:je, kb:ke])\
        -    (2.*(gx1x1[ib:ie, jb:je, kb:ke]*Ax1[ib:ie, jb:je, kb:ke]                 - gx1x1[ib:ie, jb-1:je-1, kb:ke]*Ax1[ib:ie, jb-1:je-1, kb:ke])\
        +         gx1x2[ib:ie, jb+1:je+1, kb:ke]*Ax2[ib:ie, jb+1:je+1, kb:ke]         - gx1x2[ib:ie, jb-1:je-1, kb:ke]*Ax2[ib:ie, jb-1:je-1, kb:ke]\
        +         gx1x3[ib:ie, jb:je, kb+1:ke+1]*Ax3[ib:ie, jb:je, kb+1:ke+1]         - gx1x3[ib:ie, jb-1:je-1, kb+1:ke+1]*Ax3[ib:ie, jb-1:je-1, kb+1:ke+1]\
        +         gx1x3[ib:ie, jb:je, kb:ke]*Ax3[ib:ie, jb:je, kb:ke]                 - gx1x3[ib:ie, jb-1:je-1, kb:ke]*Ax3[ib:ie, jb-1:je-1, kb:ke])/(2.*dx2*J[ib:ie, jb:je, kb:ke])
    elif field == 1:
        curl_x1 = (gx3x1[ib:ie, jb+1:je+1, kb:ke]*Ax1[ib:ie, jb+1:je+1, kb:ke]        - gx3x1[ib:ie, jb:je, kb:ke]*Ax1[ib:ie, jb:je, kb:ke]\
        +         gx3x1[ib-1:ie-1, jb+1:je+1, kb:ke]*Ax1[ib-1:ie-1, jb+1:je+1, kb:ke] - gx3x1[ib-1:ie-1, jb:je, kb:ke]*Ax1[ib-1:ie-1, jb:je, kb:ke]\
        +         gx3x2[ib:ie, jb+1:je+1, kb:ke]*Ax2[ib:ie, jb+1:je+1, kb:ke]         - gx3x2[ib:ie, jb-1:je-1, kb:ke]*Ax2[ib:ie, jb-1:je-1, kb:ke]\
        +     2.*(gx3x3[ib:ie, jb+1:je+1, kb:ke]*Ax3[ib:ie, jb+1:je+1, kb:ke]         - gx3x3[ib:ie, jb:je, kb:ke]*Ax3[ib:ie, jb:je, kb:ke]))/(2.*dx2*J[ib:ie, jb:je, kb:ke])\
        -        (gx2x1[ib:ie, jb:je, kb+1:ke+1]*Ax1[ib:ie, jb:je, kb+1:ke+1]         - gx2x1[ib:ie, jb:je, kb:ke]*Ax1[ib:ie, jb:je, kb:ke]\
        +         gx2x1[ib-1:ie-1, jb:je, kb+1:ke+1]*Ax1[ib-1:ie-1, jb:je, kb+1:ke+1] - gx2x1[ib-1:ie-1, jb:je, kb:ke]*Ax1[ib-1:ie-1, jb:je, kb:ke]\
        +     2.*(gx2x2[ib:ie, jb:je, kb+1:ke+1]*Ax2[ib:ie, jb:je, kb+1:ke+1]         - gx2x2[ib:ie, jb:je, kb:ke]*Ax2[ib:ie, jb:je, kb:ke])\
        +         gx2x3[ib:ie, jb:je, kb+1:ke+1]*Ax3[ib:ie, jb:je, kb+1:ke+1]         - gx2x3[ib:ie, jb:je, kb-1:ke-1]*Ax3[ib:ie, jb:je, kb-1:ke-1])/(2.*dx3*J[ib:ie, jb:je, kb:ke])
        curl_x2 = (2.*(gx1x1[ib:ie, jb:je, kb+1:ke+1]*Ax1[ib:ie, jb:je, kb+1:ke+1]    - gx1x1[ib:ie, jb:je, kb:ke]*Ax1[ib:ie, jb:je, kb:ke])\
        +         gx1x2[ib:ie, jb:je, kb+1:ke+1]*Ax2[ib:ie, jb:je, kb+1:ke+1]         - gx1x2[ib:ie, jb:je, kb:ke]*Ax2[ib:ie, jb:je, kb:ke]\
        +         gx1x2[ib:ie, jb-1:je-1, kb+1:ke+1]*Ax2[ib:ie, jb-1:je-1, kb+1:ke+1] - gx1x2[ib:ie, jb-1:je-1, kb:ke]*Ax2[ib:ie, jb-1:je-1, kb:ke]\
        +         gx1x3[ib:ie, jb:je, kb+1:ke+1]*Ax3[ib:ie, jb:je, kb+1:ke+1]         - gx1x3[ib:ie, jb:je, kb-1:ke-1]*Ax3[ib:ie, jb:je, kb-1:ke-1])/(2.*dx3*J[ib:ie, jb:je, kb:ke])\
        -        (gx3x1[ib+1:ie+1, jb:je, kb:ke]*Ax1[ib+1:ie+1, jb:je, kb:ke]         - gx3x1[ib-1:ie-1, jb:je, kb:ke]*Ax1[ib-1:ie-1, jb:je, kb:ke]\
        +         gx3x2[ib+1:ie+1, jb:je, kb:ke]*Ax2[ib+1:ie+1, jb:je, kb:ke]         - gx3x2[ib:ie, jb:je, kb:ke]*Ax2[ib:ie, jb:je, kb:ke]\
        +         gx3x2[ib+1:ie+1, jb-1:je-1, kb:ke]*Ax2[ib+1:ie+1, jb-1:je-1, kb:ke] - gx3x2[ib:ie, jb-1:je-1, kb:ke]*Ax2[ib:ie, jb-1:je-1, kb:ke]\
        +     2.*(gx3x3[ib+1:ie+1, jb:je, kb:ke]*Ax3[ib+1:ie+1, jb:je, kb:ke]         - gx3x3[ib:ie, jb:je, kb:ke]*Ax3[ib:ie, jb:je, kb:ke]))/(2.*dx1*J[ib:ie, jb:je, kb:ke])
        curl_x3 = (gx2x1[ib+1:ie+1, jb:je, kb:ke]*Ax1[ib+1:ie+1, jb:je, kb:ke]        - gx2x1[ib-1:ie-1, jb:je, kb:ke]*Ax1[ib-1:ie-1, jb:je, kb:ke]\
        +     2.*(gx2x2[ib+1:ie+1, jb:je, kb:ke]*Ax2[ib+1:ie+1, jb:je, kb:ke]         - gx2x2[ib:ie, jb:je, kb:ke]*Ax2[ib:ie, jb:je, kb:ke])\
        +         gx2x3[ib+1:ie+1, jb:je, kb:ke]*Ax3[ib+1:ie+1, jb:je, kb:ke]         - gx2x3[ib:ie, jb:je, kb:ke]*Ax3[ib:ie, jb:je, kb:ke]\
        +         gx2x3[ib+1:ie+1, jb:je, kb-1:ke-1]*Ax3[ib+1:ie+1, jb:je, kb-1:ke-1] - gx2x3[ib:ie, jb:je, kb-1:ke-1]*Ax3[ib:ie, jb:je, kb-1:ke-1])/(2.*dx1*J[ib:ie, jb:je, kb:ke])\
        -    (2.*(gx1x1[ib:ie, jb+1:je+1, kb:ke]*Ax1[ib:ie, jb+1:je+1, kb:ke]         - gx1x1[ib:ie, jb:je, kb:ke]*Ax1[ib:ie, jb:je, kb:ke])\
        +         gx1x2[ib:ie, jb+1:je+1, kb:ke]*Ax2[ib:ie, jb+1:je+1, kb:ke]         - gx1x2[ib:ie, jb-1:je-1, kb:ke]*Ax2[ib:ie, jb-1:je-1, kb:ke]\
        +         gx1x3[ib:ie, jb+1:je+1, kb:ke]*Ax3[ib:ie, jb+1:je+1, kb:ke]         - gx1x3[ib:ie, jb:je, kb:ke]*Ax3[ib:ie, jb:je, kb:ke]\
        +         gx1x3[ib:ie, jb+1:je+1, kb-1:ke-1]*Ax3[ib:ie, jb+1:je+1, kb-1:ke-1] - gx1x3[ib:ie, jb:je, kb-1:ke-1]*Ax3[ib:ie, jb:je, kb-1:ke-1])/(2.*dx2*J[ib:ie, jb:je, kb:ke])
    return curl_x1, curl_x2, curl_x3

'''

#------------------------- Cartesian -------------------------#
# Matrix xyz-position shifter with periodic boundary conditions
def shift(mat, x, y, z):
    result = np.roll(mat, -x, 0)
    result = np.roll(result, -y, 1)
    result = np.roll(result, -z, 2)
    return result

# Derivative in x
def ddx(A, s):
    return (shift(A, 1-s, 0, 0) - shift(A, 0-s, 0, 0))/dx1

# Derivative in y
def ddy(A, s):
    return (shift(A, 0, 1-s, 0) - shift(A, 0, 0-s, 0))/dx2

# Derivative in z
def ddz(A, s):
    return (shift(A, 0, 0, 1-s) - shift(A, 0, 0, 0-s))/dx3

# Curl operator
def curl(Ax, Ay, Az, s):
    curl_x = ddy(Az, s) - ddz(Ay, s)
    curl_y = ddz(Ax, s) - ddx(Az, s)
    curl_z = ddx(Ay, s) - ddy(Ax, s)
    return curl_x, curl_y, curl_z
#------------------------------------------------------------#
'''

# Divergence operator
def div(Ax1, Ax2, Ax3):
	return ((J[ib+1:ie+1, jb:je, kb:ke]*Ax1[ib+1:ie+1, jb:je, kb:ke] - J[ib:ie, jb:je, kb:ke]*Ax1[ib:ie, jb:je, kb:ke])/dx1\
    + (J[ib:ie, jb+1:je+1, kb:ke]*Ax2[ib:ie, jb+1:je+1, kb:ke] - J[ib:ie, jb:je, kb:ke]*Ax2[ib:ie, jb:je, kb:ke])/dx2\
    + (J[ib:ie, jb:je, kb+1:ke+1]*Ax3[ib:ie, jb:je, kb+1:ke+1] - J[ib:ie, jb:je, kb:ke]*Ax3[ib:ie, jb:je, kb:ke])/dx3)/J[ib:ie, jb:je, kb:ke]

# Boundary condition
def periodicBC(A):
    A_w = np.zeros([Nx1, Nx2, Nx3], dtype=float)
    A_s = np.zeros([Nx1, Nx2, Nx3], dtype=float)
    A_b = np.zeros([Nx1, Nx2, Nx3], dtype=float)
    # swop var.
    A_w[0, :, :] = A[0, :, :]
    A_s[:, 0, :] = A[:, 0, :]
    A_b[:, :, 0] = A[:, :, 0]
    # Reflective BC for A field
    A[0, :, :]  = A[-1, :, :]   # west = est
    A[-1, :, :] = A_w[0, :, :]  # est = west
    A[:, 0, :]  = A[:, -1, :]   # south = north
    A[:, -1, :] = A_s[:, 0, :]  # north = south
    A[:, :, 0]  = A[:, :, -1]   # bottom = top
    A[:, :, -1] = A_b[:, :, 0]  # top = bottom  

print('START TIME EVOLUTION...')
for t in range(Nt):
    Bx1_old[:, :, :] = Bx1[:, :, :]
    Bx2_old[:, :, :] = Bx2[:, :, :]
    Bx3_old[:, :, :] = Bx2[:, :, :]

    curl_Bx1, curl_Bx2, curl_Bx3 = curl(Bx1, Bx2, Bx3, 0)

    Ex1 += dt*curl_Bx1
    Ex2 += dt*curl_Bx2
    Ex3 += dt*curl_Bx3

    periodicBC(Ex1)
    periodicBC(Ex2)
    periodicBC(Ex2)

    curl_Ex1, curl_Ex2, curl_Ex3 = curl(Ex1, Ex2, Ex3, 1)

    Bx1 -= dt*curl_Ex1
    Bx2 -= dt*curl_Ex2
    Bx3 -= dt*curl_Ex3

    periodicBC(Bx1)
    periodicBC(Bx2)
    periodicBC(Bx2)

    #U[t] = 0.5*np.sum(Ex1**2 + Ex2**2 + Ex3**2 + Bx1*Bx1_old + Bx2*Bx2_old + Bx3*Bx3_old)
    U[t] =  0.5 * np.sum(Ex1[ib:ie, jb:je, kb:ke]**2 + Ex2[ib:ie, jb:je, kb:ke]**2 + Ex2[ib:ie, jb:je, kb:ke]**2\
    + Bx1[ib:ie, jb:je, kb:ke]*Bx1_old[ib:ie, jb:je, kb:ke] + Bx2[ib:ie, jb:je, kb:ke]*Bx2_old[ib:ie, jb:je, kb:ke] + Bx3[ib:ie, jb:je, kb:ke]*Bx3_old[ib:ie, jb:je, kb:ke])
    divB[t] = np.sum(np.abs(div(Bx1, Bx2, Bx3)))
    print('t step: ', t)
'''
    plt.subplot(2, 2, 1)
    plt.pcolor(x1v, x2v, Bx3)
    plt.colorbar()
    plt.subplot(2, 2, 2)
    plt.plot(divB)
    plt.subplot(2, 2, 3)
    plt.plot(U)
    plt.subplot(2, 2, 4)
    plt.plot(U)
'''
print('DONE!')

myplot(Ex1[:,:,0], 'Ex1')
myplot(Ex2[:,:,0], 'Ex2')
myplot(Bx3[:,:,0], 'Bx3')
myplot2(divB, 'divB vs t')
myplot2(U, 'U vs t')

plt.show()
