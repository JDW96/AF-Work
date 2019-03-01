#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 16:26:38 2019

@author: Jack
"""

import numpy as np
import Atrium_Final as AF

tot_time = 300000

parameters = np.load('parameters.npy')

full_data = []

for i in range(len(parameters)):
    full_data.append(np.load('PhaseData/onesr_data_' + str(i) + '.npy'))
    
#print(full_data[300][2][0])
    
#print(full_data[344][6][0][7])    ### 7th value is if it hits fail safe

data_num = 0

run_3k = [[0.64, 70, 0.06, 2094962020, 2094962020]]

while data_num < 50:
    
    p_rand = np.random.randint(2, 8) # Vals from 0.02 to 0.08
    job_num = np.random.randint(150, 416) * 2
    repeat_number = np.random.randint(0, 100)
    
    data = full_data[job_num][p_rand][repeat_number]
    
    
    if data[7]:
        data_num += 1
        
        run_3k.append([round(data[0])/100, round(data[1]), round(data[2])/100, round(data[4]), round(data[5])])
   
np.save('run_3k.npy', run_3k)         

def decreasing_p_large_time(run_3k, itr):

    params = run_3k[itr]
    
    nu = params[0]
    tau = params[1]
    p = params[2]
    seed1 = params[3]
    seed2 = params[4]
    
    pace = tau + 2
            
    avg_resting = None
    std_resting = None
    med_resting = None
    max_resting = None
    min_resting = None
    position_of_min = None
    position_of_max = None
    Fraction_of_resting_cells_last_timestep = None
            
    A = AF.SourceSinkModel(hexagonal=True, threshold=1, p_nonfire=p, pace_rate=pace,
                           Lx=70, Ly=100, tot_time=500000, nu_para=nu, nu_trans=nu, rp=tau,
                           seed_connections=seed1, seed_prop=seed2, 
                           charge_conservation = False, t_under = 1, t_under_on = False)

    AF_start = 40 * pace
    
    resting_cells_at_last_beat = 7000 # i.e. terminates before last beat (not possible)
    
    np.random.seed(A.seed_prop)

    A.cmp_timestep()   ### With one sinus beat       
            
    while A.stop == False:
        if A.t < A.tot_time:
            
            if A.t == 31 * A.pace_rate: # fraction of resting cells at the last beat
                resting_cells_at_last_beat = len(A.resting_cells[A.resting_cells == True])/(A.Lx*A.Ly)
            
            if A.t < 31 * A.pace_rate:
                # pacing
                A.pacing_with_change_of_rp(time_between_pace_and_change_of_rp = 0,
                         increment = -1)

                A.find_propagation_time() # time till first cell in last column excites for the first time
                
                if A.propagated == True:
                    AF_start = int((31 * pace) + (5 * A.propagation_time))
            
            else:
                if len(A.states[0]) != 0:   # continues to propagate
                    
                    if A.t % 2000 == 0 and A.p_nonfire > 0.0006:
                        A.p_nonfire -= 0.0003
                
                    A.cmp_no_sinus()
                    
                    if A.t > AF_start:
                        A.t_AF += 1
                        A.resting_cells_over_time_collect()

                else:
                    # terminates
                    A.time_extinguished = A.t
                    A.stop = True
                    
                    Fraction_of_resting_cells_last_timestep = len(A.resting[A.resting == True]) / (A.Lx * A.Ly)
                    
                    
        else:
            # reaches tot_time
            A.fail_safe = True
            A.time_extinguished = A.t
            A.stop = True

            Fraction_of_resting_cells_last_timestep = len(A.resting[A.resting == True]) / (A.Lx * A.Ly)
            
    
    if A.t_AF > 0:
        A.AF = True
    
    if len(A.resting_cells_over_time) > 200:     ### Want to ignore last 200 values
    
        resting_cells_minus_slice = np.array(A.resting_cells_over_time[:-200])
    
        avg_resting = np.mean(resting_cells_minus_slice) / (A.Lx * A.Ly)    
        std_resting = np.std(resting_cells_minus_slice) / (A.Lx * A.Ly)
        med_resting = np.median(resting_cells_minus_slice) / (A.Lx * A.Ly)
        max_resting = max(resting_cells_minus_slice) / (A.Lx * A.Ly)
        min_resting = min(resting_cells_minus_slice) / (A.Lx * A.Ly)
        
        position_of_min = np.where(resting_cells_minus_slice == min(resting_cells_minus_slice))[0][0] + AF_start # time of min
        position_of_max = np.where(resting_cells_minus_slice == max(resting_cells_minus_slice))[0][0] + AF_start # time of max
        
        
    # nu
    # tau
    # p
    ### whether the charge under threshold is conserved
    ### pace_rate
    ### nu_para/nu_trans
    # repeat number
    # seed_connection
    # seed_propagation
    # A.fail_safe = whether it extinguishes at tot_time
    # A.AF = whether it eneters AF
    # A.t_AF = how long it was in AF for
    # A.time_extinguished = time wave is extinguished == tot_time if doesn't terminate
    # time of AF starting
    # average number of resting cells
    # std of number of resting cells
    # median of number of resting cells
    # min of number of resting cells
    # max of number of resting cells
    # fraction of resting cells at last beat
    # fraction of resting cells at last time step either self.states[0] == 0 or self.t == tot_time
    # position of min
    # position of max
    
    data = np.array([nu*100, tau, p*100, 
                     A.seed_connections, A.seed_prop,
                     A.fail_safe, A.AF, A.t_AF, A.time_extinguished, AF_start, avg_resting, std_resting,
                     med_resting, min_resting, max_resting, resting_cells_at_last_beat,
                     Fraction_of_resting_cells_last_timestep, 
                     position_of_min, position_of_max])

    np.save('long_run_decrease_p' + str(itr) + '.npy', data)






    
#    print(full_data[344][6][0][i])
    
    
    
    