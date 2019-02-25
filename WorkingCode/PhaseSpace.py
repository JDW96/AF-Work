
import numpy as np
import sys
import math
import Atrium_Final as AF

#job_number = int(sys.argv[1])


#input_param = np.load('parameters.npy')
#input_seeds = np.load('seeds.npy')

#print(np.shape(input_param))

def OnePacemakerBeat(parameters, seeds, itr):
    data_full = []
    
    for l in range(len(parameters[itr])):
        repeat_data = []
        print(l)
        
        for i in range(100):  ### Number of repeats   

            #print(parameters[itr][l])
            nu = parameters[itr][l][0]
            #nu_trans = nu_para/parameters[itr][l][5] # either a third or a quarter of nu_para

            tau = int(parameters[itr][l][1])
            p = parameters[itr][l][2]
            t_under_on = False # parameters[itr][l][3]
            pace = tau + 2
            
            avg_resting = None
            std_resting = None
            med_resting = None
            max_resting = None
            min_resting = None
            
            A = AF.SourceSinkModel(hexagonal=True, threshold=1, p_nonfire=p, pace_rate=pace,
                       Lx=70, Ly=100, tot_time=15000, nu_para=nu, nu_trans=nu, rp=tau,
                       seed_connections=seeds[itr][l][i][0], seed_prop=seeds[itr][l][i][1], 
                       charge_conservation = False, t_under = 1, t_under_on = t_under_on)

            AF_start = 40 * pace
            #Number_of_resting_cells = A.Ly*A.Lx + 5

            np.random.seed(A.seed_prop)

            A.cmp_timestep()   ### With one sinus beat       
            
            while A.stop == False:
                if A.t < A.tot_time:
                    
                    if A.t < 31 * A.pace_rate:
                        A.pacing_with_change_of_rp(time_between_pace_and_change_of_rp = 0,
                                 increment = -1)
                    #if A.t < 30 * pace:
                    #    A.cmp_timestep()

                        A.find_propagation_time()
                        if A.propagated == True:
                            AF_start = int((31 * pace) + (5 * A.propagation_time))
                    
                    else:
                        if len(A.states[0]) != 0:                        
                            A.cmp_no_sinus()
                            
                            if A.t > AF_start:
                                A.t_AF += 1
                                A.resting_cells_over_time_collect()

                                #print('AF')
                                #Fraction_of_resting_cells = len(A.resting[A.resting == True])/float(A.Lx*A.Ly)
                        else:
                            A.time_extinguished = A.t
                            A.stop = True
                            #print(len(A.resting[A.resting == True]))
                            #Number_of_resting_cells = len(A.resting[A.resting == True])
                            
                            
                else:
                    A.fail_safe = True
                    A.time_extinguished = A.t
                    A.stop = True
                    #print(len(A.resting[A.resting == True]))
                    #Number_of_resting_cells = len(A.resting[A.resting == True])
                    
            #A.t_AF = int(A.time_extinguished - AF_start)
            
            if A.t_AF > 0:
                A.AF = True
            
            if len(A.resting_cells_over_time) > 0:
                avg_resting = np.mean(np.array(A.resting_cells_over_time)/(A.Lx*A.Ly))     
                std_resting = np.std(np.array(A.resting_cells_over_time)/(A.Lx*A.Ly))
                med_resting = np.median(np.array(A.resting_cells_over_time)/(A.Lx*A.Ly))
                max_resting = max(np.array(A.resting_cells_over_time)/(A.Lx*A.Ly))
                min_resting = min(np.array(A.resting_cells_over_time)/(A.Lx*A.Ly))
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
            # List of number of resting cells
            
            data = np.array([parameters[itr][l][0]*100, parameters[itr][l][1], parameters[itr][l][2]*100, 
                             i, A.seed_connections, A.seed_prop,
                             A.fail_safe, A.AF, A.t_AF, A.time_extinguished, AF_start, avg_resting, std_resting, med_resting, min_resting, max_resting])
    

    
            repeat_data.extend([data])

        data_full.extend([repeat_data])

    data_full = np.array(data_full)
    np.save('onesr_data_'+str(itr),data_full)


#OnePacemakerBeat(parameters=input_param, seeds=input_seeds, itr=job_number)

parameters = []
# nu, tau, p, whether the charge under threshold is conserved, amount to add to tau to get pace_rate 

for j in np.arange(50, 102, 2): # tau values
    for i in np.linspace(0.4, 0.7, 16, endpoint = True): # nu values
    #for i in np.linspace(0.35, 1, 4, endpoint = True):
        for k in [0,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.1,0.11,0.12,0.13,0.14,0.15,0.17,0.2,0.25,0.3]: # p values
        #for k in [0,0.5,0.9]:
            parameters.extend([[i,j,k]])
            
parameters = np.array(parameters).reshape((832,10,3))
#parameters = np.array(parameters).reshape((72,10,6))
s = np.random.randint(0, 2**31, (832, 10, 100, 2),dtype='int')
#OnePacemakerBeat(parameters, s, 27)
#np.save('parameters', parameters)
#np.save('seeds', s)

