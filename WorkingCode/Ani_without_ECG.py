
import Atrium_Final as AC
import numpy as np
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as mpat

from matplotlib import collections

# Initiating the Atrium
convolve = True

# AC.Atrium(hexagonal=False, L=200, rp=50, tot_time=10**6, nu_para=0.6, nu_trans=0.6,
#                 pace_rate=220, p_nonfire=0.05, seed_connections=1, seed_prop=4)

seed1 = 23774531
seed2 = 543192322
nu = 0.5

#rands = np.random.randint(0, 10000000, (100, 2))
#
#for elem in rands:
#    print('-------New heart-------')
#    A = AC.SourceSinkModel(hexagonal = True, pace_rate = 220, threshold = 1, p_nonfire = 0.03, L = 100, rp = 30, tot_time = 40000, nu_para=nu, nu_trans=nu,seed_connections=elem[0], seed_prop=elem[1])
#    A.cmp_full()
#    print("AF time: ", A.tot_AF)
#    print("seeds: ", elem[0], elem[1])

A = AC.SourceSinkModel(hexagonal = True, pace_rate = 220, threshold = 1, p_nonfire = 0.05, L = 100, rp = 30, tot_time = 10000, nu_para=nu, nu_trans=nu,seed_connections=seed1, seed_prop=seed2)

#A.tot_time = 100000

###############################################################################
# Animation function


def update_square(frame_number, mat, A, convolve):
    """Next frame update for animation without ECG"""
    # print(A.t)
    # print(A.phases[0])

    if A.t % 100 == 0:
        ani.event_source.stop()
        A.change_connections(1, 1)
        ani.event_source.start()

    A.cmp_animation()

    ###### WITH CONVOLUTION ######

    if convolve:
        convolution = gaussian_filter(A.phases.reshape([A.L, A.L]), sigma=1,
                                  mode=('wrap', 'nearest'))
        

        mat.set_data(convolution)
    
    ###### WITHOUT CONVOLUTION ######
    else:
        data = A.phases.reshape([A.L, A.L])
        mat.set_data(data)
    
    return mat,


def update_hex(frame_number, collection, A, convolve):    # Frame number passed as default so needed
    """Next frame update for animation without ECG"""

    A.cmp_animation()
    
    if A.AF == True:
        print('AF')

    sigma = 1.4

    if convolve:
        convolution = gaussian_filter(A.phases.reshape([A.L, A.L]), sigma=sigma,
                                      mode=('wrap', 'nearest'))
    
        data = np.ravel(convolution)
        collection.set_array(data)
        
    # WITHOUT CONVOLUTION
    else:
        collection.set_array(np.array(A.phases))


    ax.set_title('refractory period = %i, threshold = %0.2f, p not fire = %0.2f, \nseed connection = %i, seed propagation = %i, \nnu = %0.3f, t = %i, sigma = %0.1f' % (A.rp, A.threshold, A.p_nonfire, A.seed_connections, A.seed_prop, A.nu_para, A.t, sigma), fontsize=20)
    ax.title.set_position([0.5, 0.85])   

    return ax,

###############################################################################

# Running the Animation

if not A.hexagonal:
    np.random.seed(A.seed_prop)
    
    fig1 = plt.figure(figsize=[8, 5])

    ax = fig1.subplots(1, 1)
    ax.tight_layout()

    mat1 = ax.matshow(A.phases.reshape([A.L, A.L]), cmap=plt.cm.jet_r)
    mat1.set_clim(0, A.rp)
    ax.set_axis_off()
    ani = animation.FuncAnimation(fig1, update_square, frames=A.tot_time,
                                  fargs=(mat1, A, convolve), interval=100,
                                  repeat=None)

    plt.axis([0, A.L, 0, A.L])
    plt.show()

if A.hexagonal:
    np.random.seed(A.seed_prop)

    fig1 = plt.figure(figsize = [10,7])
    ax = fig1.subplots(1,1)

    patches = []
    offsets = []
    a = np.tan(np.pi/6)*0.5
    b = 0.5/np.cos(np.pi/6)
    c = 1-a-b
    
    for i in range(A.L):
        for j in range(A.L):
            
            if i % 2 == 0 and j % 2 == 0:
                offsets.extend([(j+0.5, i-(i*c))]) 
                
            elif i % 2 == 0 and j % 2 != 0:
                offsets.extend([(j + 0.5, i - (i * c))])
                
            elif i % 2 != 0 and j % 2 == 0:
                offsets.extend([(j, i - (i * c))])
                
            else:
                offsets.extend([(j, i-(i * c))])
                
    for k in offsets:
        patches.extend([mpat.RegularPolygon(k, 6, radius=0.5/np.cos(np.pi/6))])
        
    collection = collections.PatchCollection(patches, cmap= plt.cm.jet_r)

    ax.add_collection(collection, autolim=True)

    #collection.set_edgecolor('face')
    collection.set_clim(0, A.rp)

    ax.axis('equal')
    ax.set_axis_off()
    # ax.set_title('nu = %f' % A.nu_para)
    ani = animation.FuncAnimation(fig1, update_hex, frames=A.tot_time,
                                  fargs=(collection, A, convolve),
                                  interval=5, repeat=None)

    plt.axis([-1, A.L + 1, -1, A.L + 1])
    plt.show()


#ani.save('Return to SR.mp4', fps=30, dpi=250, bitrate=5000)

