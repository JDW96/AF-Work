import numpy as np
import pickle as pickle


class Atrium():
    """Creates the myocardium's structure.
    hexagonal: False = Square Lattice, True = Hexagonal Lattice
    model: 1 = standard CMP model, 2 = source-sink model
    L: Lattice length
    v_para: nu parallel 
    v_tran_1: nu transfers in square lattice or nu of main diagonal in hexagonal
    v_tran_2: nu of minor diagonal in hexagonal
    d: fraction of dysfunctional cells in standard model
    e: fraction of time that dysfunctional cells do not fire
    threshold: value equal to and above which cells always excite in the source-sink model
    p: the probability with which cells under the threshold excite in the source-sink model
    rp: refractory period
    tot_time: total time of simulation
    pace_rate: rate of pacemaker rhythm

    s1: seed for transverse connection selection
    s2: seed for parallel connection selection
    s3: seed for cell firing selection (e or p)
    """
    def __init__(self, hexagonal = False, L = 200, v_para = 1,
                 v_tran_1 = 0.1, v_tran_2 = 0.6, 
                 threshold = 0.25, p = 0.05, rp = 50, tot_time = 10**6,
                 pace_rate = 220, s1 = 1, s2 = 2, s3 = 3):
        
        # System Parameters
        self.connections_full = []
        self.hexagonal = hexagonal
        self.L = L
        
        self.transverse_prob_l = v_tran_1
        self.transverse_prob_r = v_tran_2
        self.parallel_prob = v_para  
        
        self.tot_time = tot_time
        self.rp = rp        
        self.pace_rate = pace_rate
        self.pace = np.arange(0, tot_time, pace_rate)
        
        self.p_nonfire = p_nonfire
        self.threshold = threshold
        self.p = p
            
        
        # System cell positions
        self.index = np.arange(0, L*L) # cell positions in each array
        self.position = self.index.reshape(L, L)

        self.first_col = np.arange(0, L * L, L)
        self.not_first_col = self.index[self.index % L != 0]
        self.last_col = np.arange(0, L * L, L) + L - 1
        self.last_row = np.arange((self.L * self.L) - self.L, self.L * self.L)
        
        # System seeds
        self.seed_connections = seed_connections
        self.seed_prop = seed_prop

        # Measurable Variables for AF time
        # All dummy variables that get overridden in function
        self.excitation_rate = None
        self.last_excitation = None
        self.AF = None
        self.sources = None
        self.t = None
        self.tot_AF = None  # overall
        self.t_AF = None  # in this episode
        self.t_SR = None  # in this period of SR
        self.set_AF_measuring_vars()

        # State of system
        self.phases = np.full((L * L), fill_value=self.rp)         # state cell is in (0 = excited, rp = resting)
        self.V = np.full((L * L), fill_value=-90.0)                # voltage depending on state of cell
        
        self.states = [[]] * self.rp              # list of lists containing cells in each state except resting
        self.resting = np.full([self.L**2], fill_value=True, dtype=bool)         # can they be excited
        self.to_be_excited = np.full([self.L**2], fill_value=False, dtype=bool)        # cells to be excited next timestep

        self.neighbours = None    # Dummy that gets overwritten in create_neighbours
        self.list_of_neighbours = None  # Dummy that gets overwritten in create_neighbours
        
        self.create_neighbours()

        self.neighbour_list = np.array([np.array([x for x in 
                                 self.list_of_neighbours[i] if str(x) 
                                 != 'nan'],dtype = int) for i in self.index])

    def set_AF_measuring_vars(self):
        self.excitation_rate = np.zeros(self.L**2, dtype=int)
        self.last_excitation = np.full((self.L**2), fill_value=-self.pace_rate)
        self.AF = False
        self.sources = []
        self.t = 0
        self.tot_AF = 0  # overall
        self.t_AF = 0  # in this episode
        self.t_SR = 0  # in this period of SR

    def create_neighbours(self):
        # Setting connections
        a = np.full((self.L**2), fill_value=None, dtype=float)
        
        if self.hexagonal:  # if self.hexagonal == True:
            neighbours = np.array([a] * 6)  # up_left, up_right, right, down_right, down_left, left

            np.random.seed(self.seed_connections)
            rand_nums = np.random.rand(3, self.L**2)

            num_rand_tran1 = rand_nums[0]
            num_rand_tran2 = rand_nums[1]
            num_rand_para = rand_nums[2]

            for j in self.index:

                if num_rand_para[j] <= self.nu_para:

                    if j not in self.last_col:
                        neighbours[2][j] = int(j + 1)
                        neighbours[5][j + 1] = int(j)

                # even
                if j in self.position[np.arange(0, self.L, 2)]:

                    if num_rand_tran1[j] <= self.nu_trans:

                        if j not in self.first_col:
                            neighbours[4][j] = j + self.L - 1
                            neighbours[1][j + self.L - 1] = j

                    if num_rand_tran2[j] <= self.nu_trans:
                        neighbours[3][j] = j + self.L
                        neighbours[0][j + self.L] = j

                # odd
                else:
                #if j in self.position[np.arange(1, L, 2)]:
                    if num_rand_tran1[j] <= self.nu_trans:
                        
                        if j in self.last_row: ### last row
                            neighbours[4][j] = j - ((self.L * self.L) - self.L)
                            neighbours[1][j - ((self.L * self.L) - self.L)] = j
                            
                        else:
                            neighbours[4][j] = j + self.L
                            neighbours[1][j + self.L] = j
                            

                    if num_rand_tran2[j] <= self.nu_trans:
                        if j not in self.last_col:
                            if j in self.last_row:
                                neighbours[3][j] = j - ((self.L*self.L) - self.L) + 1
                                neighbours[0][j - ((self.L*self.L) - self.L) + 1] = j
                              
                            else:    
                                neighbours[3][j] = j + self.L + 1
                                neighbours[0][j + self.L + 1] = j
                            
            self.list_of_neighbours = [[neighbours[0][i],
                                        neighbours[1][i],
                                        neighbours[2][i],
                                        neighbours[3][i],
                                        neighbours[4][i],
                                        neighbours[5][i]] for i in self.index]

            
        else:    # Square lattice
            neighbours = np.array([a] * 4)

            np.random.seed(self.seed_connections)
            num_rand_tran = np.random.rand(self.L * self.L)
            num_rand_para = np.random.rand(self.L * self.L)

            for j in self.index:

                if num_rand_para[j] <= self.nu_para:

                    if j not in self.last_col:
                        neighbours[1][j] = int(j + 1)
                        neighbours[3][j + 1] = int(j)


                if num_rand_tran[j] <= self.nu_trans:

                    if j in self.last_row:
                        neighbours[2][j] = j - ((self.L * self.L) - self.L)
                        neighbours[0][j - ((self.L * self.L) - self.L)] = j

                    else:
                        neighbours[2][j] = j + self.L
                        neighbours[0][j + self.L] = j

            self.list_of_neighbours = [[neighbours[0][i],
                                        neighbours[1][i],
                                        neighbours[2][i],
                                        neighbours[3][i]] for i in self.index]

        self.neighbours = neighbours

        self.neighbour_list = np.array([np.array([x for x in 
                                 self.list_of_neighbours[i] if str(x) 
                                 != 'nan'],dtype = int) for i in self.index])

    def change_resting_cells(self):
        self.resting[self.to_be_excited] = False    # Sets recently excited cells to False (not resting)
        self.resting[self.states[-1]] = True     # Sets previously refractory cells to resting

    def cycle_through_states(self):
        del self.states[-1]    # Pushes last cells out of states (not resting)
        self.states.insert(0, self.index[self.to_be_excited])     # Inserts new excited cells

    def relaxing(self):
        self.change_resting_cells()
        self.cycle_through_states()

    def excitation_tracker(self, excited_cells):
        self.excitation_rate[excited_cells] = self.t - self.last_excitation[excited_cells]
        self.last_excitation[excited_cells] = self.t

    def AF_checker(self, excited_cells):
        a = np.mean(self.excitation_rate[excited_cells])
        #beat = np.mean(self.excitation_rate[self.last_col])
        # if self.t > self.pace_rate:
        if a < self.pace_rate * 0.9: # and beat <= self.pace_rate * 1.5:
            self.AF = True
            self.t_AF += 1
            #print(self.AF)
            #print(self.t)

        else:
            self.AF = False

    def excite_cells(self, excited_cells):
        self.to_be_excited[excited_cells] = True

    def unexcite_cells(self, excited_cells):
        self.to_be_excited[excited_cells] = False

    def time_in_AF(self, excited_cells):
        if excited_cells.size > 0:      # Checks if non empty
            
            self.excitation_tracker(excited_cells)    # Tracks the excitation rates and last excitation of cells
            self.AF_checker(excited_cells)          # Checks and updates the AF time

    def sinus_rhythm(self):
        return None   # Dummy that gets overriden by inheriting classes

    def conduct(self):
        return None   # Dummy that gets overriden by inheriting classes

    def cmp_timestep(self):
        self.sinus_rhythm() # Now checks if correct time inside this function

        self.relaxing()    # Changes self.states, cycles cells through the refractory states

        excited_cells = self.states[0]
        if len(excited_cells) > 0:    # NOTE: added this so that the new method of finding inwards_current doesn't break the animation
            self.conduct(excited_cells)

        self.unexcite_cells(excited_cells)  # Were excited, now refractory

        self.time_in_AF(excited_cells)
        self.t += 1

    def cmp_animation(self):
        # NOTE: I moved phases above sinus_rhythm, does it make a difference???
        ######  Put sinus_rhythm() above the phases as well so that first column 
        ######  is excited in the animation. Doesn't make a difference just sets the to_be_excited values to True twice
        self.sinus_rhythm()
        
        self.phases[self.to_be_excited] = 0  # Needed for animation
        self.phases[~self.resting] += 1

        self.cmp_timestep()

    def cmp_full(self):
        np.random.seed(self.seed_prop)   # Sets seed for all dysfunctional firings etc.
        
        while self.t < self.tot_time:
            self.cmp_timestep()
            
        self.tot_AF += self.t_AF
    
    def change_connections(self,new_nu_para,new_nu_trans):
        self.nu_trans = new_nu_trans
        self.nu_para = new_nu_para
        self.create_neighbours()


class DysfuncModel(Atrium):
    
    def __init__(self, seed_dysfunc=1, dysfunctional_prob=0.05, hexagonal=False, L=200, rp=50, tot_time=10**6, nu_para=0.6, nu_trans=0.6,
                 pace_rate=220, p_nonfire=0.05, seed_connections=1, seed_prop=4):
        super(DysfuncModel, self).__init__(hexagonal, L, rp, tot_time, nu_para, nu_trans, pace_rate, p_nonfire, seed_connections, seed_prop)     # Calls Atrium init function
        
        self.seed_dysfunc = seed_dysfunc
        
        self.dysfunctional_prob = dysfunctional_prob
        self.dysfunctional_cells = np.full([self.L * self.L], fill_value=False, dtype=bool)

        self.set_dysfunctional_cells()

        functional_first_col_positions = self.dysfunctional_cells[self.first_col]

        self.first_dys = np.array(self.first_col[~functional_first_col_positions])
        self.first_fun = np.array(self.first_col[functional_first_col_positions])

    def set_dysfunctional_cells(self):
        np.random.seed(self.seed_dysfunc)
        num_rand_dysfunc = np.random.rand(self.L * self.L)

        for j in self.index:
            if self.dysfunctional_prob <= num_rand_dysfunc[j]:  # functional
                self.dysfunctional_cells[j] = True

    def sinus_rhythm(self):
        if self.t % self.pace_rate == 0:
            dysfunc_fire_rand_nums = np.random.rand(len(self.first_dys))
            successful_dysfunctional_cells = self.first_dys[dysfunc_fire_rand_nums > self.p_nonfire]

            self.excite_cells(successful_dysfunctional_cells)
            self.excite_cells(self.first_fun)

    def resting_neighbours(self, excited_cells):
        if self.hexagonal:
            neighbours = np.array([self.neighbours[0][excited_cells], self.neighbours[1][excited_cells],
                                   self.neighbours[2][excited_cells], self.neighbours[3][excited_cells],
                                   self.neighbours[4][excited_cells], self.neighbours[5][excited_cells]])

        if not self.hexagonal:  # square lattice, rarely used so ignore check
            neighbours = np.array([self.neighbours[0][excited_cells], self.neighbours[1][excited_cells],
                                   self.neighbours[2][excited_cells], self.neighbours[3][excited_cells]])

        neighbours = np.array(neighbours[~np.isnan(neighbours)], dtype=int)
        neighbours = neighbours[self.resting[neighbours]]

        return neighbours

    def get_dysfunctional_neighbour_indices(self, neighbours):

        return self.dysfunctional_cells[neighbours]

    def conduct(self, excited_cells):
        neighbours = self.resting_neighbours(excited_cells)

        dysfunc_neighbour_indices = self.get_dysfunctional_neighbour_indices(neighbours)

        func_neighbours = neighbours[dysfunc_neighbour_indices]
        dysfunc_neighbours = neighbours[~dysfunc_neighbour_indices]

        dysfunc_fire_rand_nums = np.random.rand(len(dysfunc_neighbours))
        dysfunc_neighbours = dysfunc_neighbours[dysfunc_fire_rand_nums > self.p_nonfire]

        self.excite_cells(func_neighbours)
        self.excite_cells(dysfunc_neighbours)


class SourceSinkModel(Atrium):
    
    def __init__(self, threshold=0.5, hexagonal=True, L=100, rp=30, tot_time=5*10**3, nu_para=0.95, nu_trans=0.95,
                 pace_rate=220, p_nonfire=0.5, seed_connections=3667261, seed_prop=874975):
        super(SourceSinkModel, self).__init__(hexagonal, L, rp, tot_time, nu_para, nu_trans, pace_rate, p_nonfire, seed_connections, seed_prop)       # Calls Atrium init function

        self.threshold = threshold

    def sinus_rhythm(self):
        if self.t % self.pace_rate == 0:
            self.to_be_excited[self.first_col] = True

    def get_inward_current(self, neighbours_list,resting_neighbours):
        inward_current = np.zeros(self.L**2)
        
        for i in neighbours_list:

            if len(i) != 0:
                inward_current[i] += float(1)/ len(i)
                
        return inward_current

    def cells_miss_threshold(self, receive_current, inward_current):
        possible_excited = receive_current[inward_current[receive_current] < self.threshold]
        #print(possible_excited)
        miss_threshold_fire_rand_nums = np.random.rand(len(possible_excited))
        possible_excited = possible_excited[miss_threshold_fire_rand_nums > self.p_nonfire + self.threshold - inward_current[possible_excited]]  # Fire if over p_nonfire
        
        return possible_excited

    def find_resting_neighbours(self, excited_cells):
        ###### NOTE: replaced line 387 with 388 for speed
        # neighbours_list = [[y for y in self.neighbour_list[i] if self.resting[int(y)]] for i in excited_cells]
        neighbours_list = [j[self.resting[j]] for j in self.neighbour_list[excited_cells]]
        
        resting_neighbours = list(map(len, neighbours_list))

        return neighbours_list, resting_neighbours

    def conduct(self, excited_cells):
        neighbours_list, resting_neighbours = self.find_resting_neighbours(excited_cells)
        
        inward_current = self.get_inward_current(neighbours_list,resting_neighbours)  # amount of current received
        
        receive_current = self.index[inward_current > 0]  # Indices which receive any current from neighbours
        self.connections.extend(inward_current[receive_current])
        hit_thresh_so_excite = receive_current[inward_current[receive_current] >= self.threshold]
        miss_thresh_but_still_excite = self.cells_miss_threshold(receive_current, inward_current)

        ###### NOTE: Removed the use of the excite_cells() to save a tiny amount of time
        self.to_be_excited[miss_thresh_but_still_excite] = True
        self.to_be_excited[hit_thresh_so_excite] = True

nu = np.linspace(0.34,1,34)
all_data = []
for i in nu:
    print(i)
    data = []
    sc = np.random.rand(50)
    sp = np.random.rand(50)
    for j in range(50):
        A = SourceSinkModel(threshold=0.5, hexagonal=True, L=100, rp=30, tot_time=5*10**3, nu_para=i, nu_trans=i,
                 pace_rate=220, p_nonfire=0.5, seed_connections=int(sc[j]), seed_prop=int(sp[j]))
        A.cmp_full()
        stats = np.unique(A.connections,return_counts= True)
        data.extend([stats])
        
    all_data.extend([[i,data]])
pickle.dump( all_data, open( "connection_data_set1_t0.5_p0.5.p", "wb" ) )
=======
        
        #System seeds
        self.seed_connect_tran = s1
        self.seed_connect_para = s2
        self.seed_prop = s3

        # Measurable Variables
        self.excitation_rate = np.zeros(L*L, dtype = int)
        self.last_excitation = np.full((L*L), fill_value = -self.pace_rate)
        self.AF = False
        self.fail_safe = False
        self.stop = False
        self.time_extinguished = 0
        #self.sources  = []
        self.t = 0
        self.tot_AF = 0 # overall
        self.t_AF = 0 # in this episode
        #self.t_SR = 0 # in this period of SR

        # Neighbours
        a = np.full((L*L),fill_value = None,dtype = float)
        self.neighbours = np.array([a]*6)      

        # State of system
        
        self.states = [[]]*self.rp # list of lists containing cells in each state except resting
        self.resting = np.full([L*L],fill_value = True, dtype = bool) # can they be excited
        self.tbe = np.full([L*L],fill_value = False, dtype = bool) # cells to be excited in next timestep
        
        # Setting connections and dysfunctional cells
         

        np.random.seed(self.seed_connect_tran)
        num_rand_tran1 = np.random.rand(L*L)
        num_rand_tran2 = np.random.rand(L*L)
        
        
        np.random.seed(self.seed_connect_para)
        num_rand_para = np.random.rand(L*L)
        
                    
        for j in self.index:
            
            if num_rand_para[j] <= self.parallel_prob:
                
                if j in self.last_col:
                    self.neighbours[2][j] = None
                    
                else:
                    self.neighbours[2][j] = int(j + 1)
                    self.neighbours[5][j + 1] = int(j)
        
        for j in self.index:
            #even
            if j in self.position[np.arange(0, L, 2)]:
                
                if num_rand_tran1[j] <= self.transverse_prob_l:
                    
                    if j not in self.first_col:
                        self.neighbours[4][j] = j + L - 1
                        self.neighbours[1][j + L - 1] = j
                        
                if num_rand_tran2 [j] <= self.transverse_prob_r:
                    
                    self.neighbours[3][j] = j + L
                    self.neighbours[0][j + self.L] = j
                    
            #odd
            else:
            #if j in self.position[np.arange(1, L, 2)]:
                
                if j in np.arange(self.L * self.L - self.L, self.L * self.L): ### last row
                    
                    if num_rand_tran1[j] <= self.transverse_prob_l:
                        self.neighbours[4][j] = j - ((self.L * self.L) - self.L)
                        self.neighbours[1][j - ((self.L * self.L) - self.L)] = j

                else:
                    
                    if num_rand_tran1[j] <= self.transverse_prob_l:
                        self.neighbours[4][j] = j+L
                        self.neighbours[1][j + self.L] = j
                        
                if num_rand_tran2 [j] <= self.transverse_prob_r:
                    
                    if j not in self.last_col:
                        
                        if j in np.arange(self.L * self.L - self.L, self.L * self.L):
                            self.neighbours[3][j] = j - ((self.L*self.L) - self.L) + 1
                            self.neighbours[0][j - ((self.L*self.L) - self.L) + 1] = j
                            
                        else:    
                            self.neighbours[3][j] = j + self.L + 1
                            self.neighbours[0][j + self.L + 1] = j
                            
            
        self.list_of_neighbours =  [[self.neighbours[0][i],
             self.neighbours[1][i],
             self.neighbours[2][i],
             self.neighbours[3][i],
             self.neighbours[4][i],
             self.neighbours[5][i]] for i in self.index]  
        
            
        self.neighbour_list = np.array([[x for x in 
                                 self.list_of_neighbours[i] if str(x) 
                                 != 'nan'] for i in self.index])
            
    def SinusRhythm(self):
        
            self.tbe[self.first_col] = True
           
    def Relaxing(self):

        self.resting[self.tbe] = False
        self.resting[self.states[-1]] = True
        
        del self.states[-1]
        self.states.insert(0, self.index[self.tbe])

    
    def Conduct(self):
        
        x = self.states[0]
            
        neighbours_list = [[y for y in self.neighbour_list[i] if self.resting[int(y)] == True] for i in x]

        resting_neighbours = list(map(len,neighbours_list))
        #print(resting_neighbours)
        inward_current = np.zeros(self.L * self.L)
        number_of_excited_cells_connected = np.zeros(self.L * self.L)
        single_connections = np.empty(sum(resting_neighbours),dtype = tuple)
        
        
        for i in range(len(neighbours_list)):
            
            if resting_neighbours[i] != 0:
                inward_current[np.array(neighbours_list[i],dtype = int)] += float(1) / resting_neighbours[i]
                number_of_excited_cells_connected[np.array(neighbours_list[i],dtype = int)] += 1
        
        complete_connections = [[]] * len(inward_current)
        k = int(0) 
        for i in range(len(neighbours_list)):
            for j in neighbours_list[i]:
                #print(j)
                complete_connections[int(j)] = np.append(complete_connections[int(j)],resting_neighbours[int(i)])
                #print(np.array(complete_connections))
                single_connections[k] = (resting_neighbours[int(i)],int(number_of_excited_cells_connected[int(j)]))
                k += 1
            
        #print(resting_neighbours.reshape(self.L,self.L))
        #print(number_of_excited_cells_connected.reshape(self.L,self.L))
        #print(x)
        #print(neighbours_list)
        #print(single_connections)
        complete_connections = [complete_connections[i] for i in range(len(complete_connections)) if len(complete_connections[i]) != 0]
        #print(np.array(complete_connections))#.reshape(self.L,self.L))
        self.connections_full.extend([complete_connections])
        receive_current = self.index[inward_current > 0]
        
        get_excited = receive_current[inward_current[receive_current] >= self.threshold]
        
        possible_excited = receive_current[inward_current[receive_current] < self.threshold]
        e_comp_val3 = np.random.rand(len(possible_excited))
        possible_excited = possible_excited[e_comp_val3 <= self.p]

        self.tbe[possible_excited] = True
        self.tbe[get_excited] = True
        
        self.tbe[x] = False
        
    


    def TimeInAF(self):

        if len(self.states[0]) > 0: 
            
            x = self.states[0]
            
            self.excitation_rate[x] = np.abs(self.last_excitation[x] - self.t)
            self.last_excitation[x] = self.t
        
            a = np.mean(self.excitation_rate[x])

            if a < self.pace_rate * 0.9:
                self.AF = True
                self.tot_AF += 1
            
            else:
                self.AF = False

    def CMP2D_timestep(self):

        if np.remainder(self.t, self.pace_rate) == 0:
            self.SinusRhythm()
            
        self.Relaxing()
        self.Conduct()

        self.TimeInAF()
        self.t += 1
        
    def CMP2D(self):

        np.random.seed(self.seed_prop)
        
        while self.t < self.tot_time:
 
            self.CMP2D_timestep()
        
A = Atrium(hexagonal = True,L = 20, v_para = 0.5,
                     v_tran_1 = 0.5, v_tran_2 = 0.5,
                     threshold = 0.2, p = 0.25, rp = 50, tot_time = 20,
                     pace_rate = 220, s1 = 10, s2 = 40, s3 = 30)
A.CMP2D()
>>>>>>> 9ef767596c9c4cc3e3587084cba1fb3187197814
