#Imports
import sys, subprocess  # To run the .dat file with Sofistik
import os               # for the environment variable necessary, this is a great tool
import platform         # checks the python platform
import string
from ctypes import *    # read the functions from the cdb
from sofistik_daten import *
import numpy as np
import math
import matplotlib.pyplot as plt
from openpyxl import Workbook
import matplotlib.ticker as ticker



#open the .dat file
def opening_dat_file(dat_file):
    Data_array = []
    with open(dat_file, 'r') as file:
        for line in file:
            columns = line.split()
            if columns != []:  #skip the empty lines
                Data_array.append(columns) 
    return Data_array


#edit the cross-section of the beam 
def editing_cross_section_dat_file(data_array, height,width,tw,tf):
    for i in range(len(data_array)):
        if data_array[i][0] == 'sto#Hw':
            data_array[i][1] = str(height)
        if data_array[i][0] == 'sto#Bf':
            data_array[i][1] = str(width)
        if data_array[i][0] == 'sto#tw':
            data_array[i][1] = str(tw)
        if data_array[i][0] == 'sto#tf':
            data_array[i][1] = str(tf)
                                 
    return data_array

#edit the concrete class of the beam 
def editing_concrete_class_dat_file(data_array, concrete_class):
    for i in range(len(data_array)):
        if data_array[i][0] == 'conc':
            for j in range(len(data_array[i])):
                if data_array[i][j] == 'fcn':
                    data_array[i][j+1] = str(concrete_class)
    return data_array

#edit the steel type of the beam 
def editing_steel_class_dat_file(data_array, steel_type):
       
    for i in range(len(data_array)):
        if data_array[i][0] == 'sto#STEELCLASS':
            data_array[i][1] = str(steel_type)                
    return data_array

#Store the data to a new .dat file
def store_to_new_dat_file(new_data, dat_file_store):
    with open(dat_file_store, 'w') as file:
        for lines in new_data:
            for i in lines:
                file.write(str(i))
                file.write('\t')
            file.write('\n')
    print('New File stored')
    return

#Running a .dat file in Sofistik
def running_dat_file(dat_file):
    sps_app = r'C:\Program Files\SOFiSTiK\2024\SOFiSTiK 2024\sps.exe'
    subprocess.run([sps_app, dat_file])
    print('Running .dat file completed')
    return

#Getting the DLLS functions
def get_the_DLLs_functions():
    # Check the python platform (32bit or 64bit)
    sofPlatform = str(platform.architecture())
    # Get the DLLs (32bit or 64bit DLL)
    if sofPlatform.find("32Bit") < 0:
        # Set environment variable for the dll files
        print ("Hint: 64bit DLLs are used")

        # Set DLL dir path - new in PY 3.8 for ctypes
        # See: https://docs.python.org/3/whatsnew/3.8.html#ctypes
        os.add_dll_directory(r"C:\Program Files\SOFiSTiK\2024\SOFiSTiK 2024\interfaces\64bit")
        os.add_dll_directory(r"C:\Program Files\SOFiSTiK\2024\SOFiSTiK 2024")

        # Get the DLL functions
        myDLL = cdll.LoadLibrary("sof_cdb_w_edu-2024.dll")
        py_sof_cdb_get = cdll.LoadLibrary("sof_cdb_w_edu-2024.dll").sof_cdb_get
        py_sof_cdb_get.restype = c_int

        py_sof_cdb_kenq = cdll.LoadLibrary("sof_cdb_w_edu-2024.dll").sof_cdb_kenq_ex
        py_sof_cdb_kexist = cdll.LoadLibrary("sof_cdb_w_edu-2024.dll").sof_cdb_kexist
    else:
        print ("Hint: 32bit DLLs are used")
        return

    return myDLL, py_sof_cdb_get, py_sof_cdb_kenq, py_sof_cdb_kexist

#Open the cdb file
def opening_cdb_file(cdb_file, myDLL):
    Index = c_int()
    cdbIndex = 99
    Index.value = myDLL.sof_cdb_init(cdb_file.encode('utf-8'), cdbIndex)

    #get the cdb status
    cdbStat = c_int()
    cdbStat.value = myDLL.sof_cdb_status(Index.value)
    print('CDB Status:', cdbStat.value)
    return Index

#Closing the cdb file
def closing_cdb_file(myDLL):
    myDLL.sof_cdb_close(0)
    return

#Reading the stresses of the beam
def stresses_beam_max(Index, py_sof_cdb_kexist, py_sof_cdb_get):
    sig_c = 0.0 #compressive stress in the conrete
    sig_t = 0.0 #tensile stress in the steel
    if py_sof_cdb_kexist(105, 100) == 2: # the key exists and contains data
        print('yes max stresses')
        ie = c_int(0)       
        RecLen = c_int(sizeof(cbeam_stc))
        while ie.value == 0:
            ie.value = py_sof_cdb_get(Index, 105, 100, byref(cbeam_stc), byref(RecLen), 1)
            if cbeam_stc.m_mnr == 1414480467: #material number of the stress point defined (found in database)
                sig_t = cbeam_stc.m_sigt    
            if cbeam_stc.m_mnr == 1347376195: #material number of the stress point defined (found in database)
                sig_c = cbeam_stc.m_sigc    
            RecLen = c_int(sizeof(cbeam_stc))
    return sig_c, sig_t


#reading height and width of the beam (sharon)
def width_and_height_beam(Index, py_sof_cdb_kexist, py_sof_cdb_get):
    if py_sof_cdb_kexist(9, 1) == 2: # the key exists and contains data
        print('yes width and height')
        ie = c_int(0)
        RecLen = c_int(sizeof(csect_rec))
        while ie.value == 0:
            ie.value = py_sof_cdb_get(Index, 9, 1, byref(csect_rec), byref(RecLen), 1)
            if csect_rec.m_id == 10.0:
                b = csect_rec.m_b
                h = csect_rec.m_h
                su = csect_rec.m_su
                so = csect_rec.m_so
            RecLen = c_int(sizeof(csect_rec))
    return b, h 

#reading Beam properties (unfinished)
def beam_properties(Index, py_sof_cdb_kexist, py_sof_cdb_get):
    
    Area_profile_steel = 0 #in m^2
    Area_profile_concrete = 0 #in m^2
    
    if py_sof_cdb_kexist(9, 1) == 2: # the key exists and contains data
        
        ie = c_int(0)
        RecLen = c_int(sizeof(csect_par))
        while ie.value == 0:
            ie.value = py_sof_cdb_get(Index, 9, 1, byref(csect_par), byref(RecLen), 1)
            k = csect_par.m_a
            print (k)
            if csect_par.m_mno == 1:
                Area_profile_steel= csect_par.m_a
            if csect_par.m_mrf == 3:    
                Area_profile_concrete= csect_par.m_a
            RecLen = c_int(sizeof(csect_par))
            
           
    return Area_profile_steel, Area_profile_concrete 

def beam_properties2(Index, py_sof_cdb_kexist, py_sof_cdb_get):
    
    Area_profile_steel = 0 #in m^2
    Area_profile_concrete = 0 #in m^2
    
    if py_sof_cdb_kexist(9, 1) == 2: # the key exists and contains data
        
        ie = c_int(0)
        RecLen = c_int(sizeof(csect_par))
        
        while ie.value == 0:
            ie.value = py_sof_cdb_get(Index, 9, 1, byref(csect_par), byref(RecLen), 1)
            k = csect_par.m_a
            print (k)
            print('test')
            RecLen = c_int(sizeof(csect_par))
            
    return Area_profile_steel, Area_profile_concrete 

def beam_propertiestemp(data_edited):
    for i in range(len(data_edited)):
                                if data_edited[i][0] == 'sto#W':
                                        Bc = 1000*float(data_edited[i][1])
                                if data_edited[i][0] == 'sto#Hw':
                                        Hw = float(data_edited[i][1])
                                if data_edited[i][0] == 'sto#tw':
                                        tw = float(data_edited[i][1])
                                if data_edited[i][0] == 'sto#Bf':
                                        Bf = float(data_edited[i][1])
                                if data_edited[i][0] == 'sto#tf':
                                        tf = float(data_edited[i][1])
                                if data_edited[i][0] == 'Sto#tc':
                                        tc = float(data_edited[i][1])                                  
    As = (2*Bf*tf+Hw*tw)/1000/1000
    Ac = (Bc*tc )/1000/1000
    Circ_ext = (2*(2*tf+2*Bf)-Bf-2*tw+2*Hw )/1000  
                    
    return(As,Ac,Circ_ext)       

#reading normal force and moment
def Internal_forces_beam_max(Index, py_sof_cdb_kexist, py_sof_cdb_get):
    if py_sof_cdb_kexist(102, 1001) == 2: # the key exists and contains data
        print('yes internal forces')
        ie = c_int(0)
        Ned = 0.0
        Med = 0.0
        RecLen = c_int(sizeof(cbeam_foc))
        while ie.value == 0:
            ie.value = py_sof_cdb_get(Index, 102, 1, byref(cbeam_foc), byref(RecLen), 1)
            if cbeam_foc.m_id == 0.0:
                if abs(Ned) < abs(cbeam_foc.m_n) and abs(cbeam_foc.m_n < 1e+30):
                    Ned = cbeam_foc.m_n
                if abs(Med) < abs(cbeam_foc.m_my) and cbeam_foc.m_my < 1e+30:
                    Med = cbeam_foc.m_my
            RecLen = c_int(sizeof(cbeam_foc))
    return Ned, Med

#reading moment
def Moment_beam_max(Index, py_sof_cdb_kexist, py_sof_cdb_get):
    Med = 0.0
    if py_sof_cdb_kexist(102, 100) == 2: # the key exists and contains data
        print('yes Med')
        ie = c_int(0)
        
        RecLen = c_int(sizeof(cbeam_foc))
        while ie.value == 0:
            ie.value = py_sof_cdb_get(Index,102, 100, byref(cbeam_foc), byref(RecLen), 1)
            if cbeam_foc.m_id == 0.0:               
                if abs(Med) < abs(cbeam_foc.m_my) and cbeam_foc.m_my < 1e+30:
                    Med = cbeam_foc.m_my
            RecLen = c_int(sizeof(cbeam_foc))
    return  Med

#reading steel properties
def fy_beam(Index, py_sof_cdb_kexist, py_sof_cdb_get,matnumber):
    if py_sof_cdb_kexist(1, matnumber) == 2: # the key exists and contains data
        #print('yes fy')
        fyk = 600
        rho = 0
        ie = c_int(0)
        RecLen = c_int(sizeof(cmat_stee))
        while ie.value < 2:
            ie.value = py_sof_cdb_get(Index, 1, matnumber, byref(cmat_stee), byref(RecLen), 1)
            if cmat_stee.m_id == 1.0:
                fyk = cmat_stee.m_fy
                rho = cmat_stee.m_rho
            RecLen = c_int(sizeof(cmat_stee))
        #print('fyk=',fyk)
    return fyk, rho

#reading concrete properties
def fc_beam(Index, py_sof_cdb_kexist, py_sof_cdb_get):
    if py_sof_cdb_kexist(1, 3) == 2: # the key exists and contains data
        #print('yes fc')
        fck = 40
        rho = 0
        ie = c_int(0)
        RecLen = c_int(sizeof(cmat_conc))
        while ie.value < 2:
            ie.value = py_sof_cdb_get(Index, 1, 4, byref(cmat_conc), byref(RecLen), 1)
            if cmat_conc.m_id == 1.0:
                fck = cmat_conc.m_fck
                rho = cmat_conc.m_rho
            RecLen = c_int(sizeof(cmat_stee))
    return fck, rho

    
    #Check if stresses are allowed 
def CHECK_stresses(sig_c_max, sig_t_max, fyk,fck):
    if abs(sig_c_max) <= fck and abs(sig_t_max) <= fyk:
        print('stresses are within limit')
        
        return True
    else:
        print('stresses are NOT within limit')
        return False

 
    #write excel file
def write_excel_file(All_possible_profiles): 
    wb = Workbook() # creates a workbook object.
    ws = wb.active # creates a worksheet object.

    for row in All_possible_profiles:
        ws.append(row) # adds values to cells, each list is a new row.
    
    wb.save("excel_files/profiles_L50_B12_2500.xlsx") # save to excel file.





def plot_filtered_samples(All_possible_profiles,filter_parameter):
    
    co2_array = []
    price_array = []
    number_array = []

    for j in range(len(All_possible_profiles)):
         for k in range(len(All_possible_profiles[j])):
            if All_possible_profiles[j][k] == filter_parameter:
                co2_array.append(All_possible_profiles[j][9])
                price_array.append(All_possible_profiles[j][10])
                number_array.append(All_possible_profiles[j][0])
             
    plt.clf()

    xs = co2_array
    ys = price_array
    zs = number_array

    plt.scatter(xs,ys)
    plt.xlabel("kg CO2e")
    plt.ylabel("price [euro]")

    for x,y,z in zip(xs,ys,zs):

        label = f"{z}"

        plt.annotate(label, # this is the text
                    (x,y), # these are the coordinates to position the label
                    textcoords="offset points", # how to position the text
                    xytext=(0,10), # distance from text to points (x,y)
                    ha='center') # horizontal alignment can be left, right or center
        plt.savefig("excel_files/figure.png")
    plt.show()

def plot_filtered_samples2(All_possible_profiles,parameter1,parameter2):
    
    co2_array = []
    price_array = []
    number_array = []

    for j in range(len(All_possible_profiles)):
        for k in range(len(All_possible_profiles[j])):
            for l in range(len(All_possible_profiles[j])):

                if ((All_possible_profiles[j][k] == parameter1)  and (All_possible_profiles[j][l] == parameter2))  :
                    co2_array.append(All_possible_profiles[j][9])
                    price_array.append(All_possible_profiles[j][10])
                    number_array.append(All_possible_profiles[j][0])


        # for i in range(len(All_possible_profiles)-1):
        #         if All_possible_profiles[i+1][9]>max_co2:
        #             max_co2 = All_possible_profiles[i+1][9]
        #         if All_possible_profiles[i+1][9]<min_co2:
        #             min_co2 = All_possible_profiles[i+1][9]       
        #         if All_possible_profiles[i+1][10]>max_price:
        #             max_price = All_possible_profiles[i+1][10]
        #         if All_possible_profiles[i+1][10]<min_price:
        #             min_price = All_possible_profiles[i+1][10]

                
    plt.clf()

     # using some dummy data for this example
    xs = co2_array
    ys = price_array
    zs = number_array

    plt.scatter(xs,ys)
    plt.xlabel("kg CO2e")
    plt.ylabel("price [euro]")

    for x,y,z in zip(xs,ys,zs):

            label = f"{z}"

            plt.annotate(label, # this is the text
                        (x,y), # these are the coordinates to position the label
                        textcoords="offset points", # how to position the text
                        xytext=(0,10), # distance from text to points (x,y)
                        ha='center') # horizontal alignment can be left, right or center
            plt.savefig("excel_files/figure.png")
    plt.show()

from matplotlib.patches import Patch
import matplotlib.cm as cm
import matplotlib.colors as mcolors


def plot_filtered_samples3(All_possible_profiles):
    material_legend = {
    0.0: 'Construction steel S355',
    0.2: 'Duplex stainless steel 2205',
    0.4: 'Recycled construction steel S355',
    0.6: 'Construction steel S450',
    0.8: 'Recycled construction steel S450',
    1.0: 'Weathering steel S355'
    }

    # Normalize and colormap
    norm = mcolors.Normalize(vmin=0.0, vmax=1.0)
    cmap = cm.get_cmap('viridis')

    # Create legend handles
    handles = [
        Patch(color=cmap(norm(value)), label=label)
        for value, label in material_legend.items()
        ]
    
    co2_array = []
    price_array = []
    number_array = []
    material_array = []


    for j in range(len(All_possible_profiles)-1):
         #for k in range(len(All_possible_profiles[j])):
            #if All_possible_profiles[j][k] == filter_parameter:
                co2_array.append(All_possible_profiles[j+1][9])
                price_array.append(All_possible_profiles[j+1][10])
                number_array.append(All_possible_profiles[j+1][0])
                if All_possible_profiles[j+1][6] == 'construction steel S355':
                     material_array.append(0.0)
                if All_possible_profiles[j+1][6] == 'Recycled Construction steel S355':
                     material_array.append(0.4)
                if All_possible_profiles[j+1][6] == 'Weathering steel S355':
                     material_array.append(1.0)
                if All_possible_profiles[j+1][6] == 'construction steel S450':
                     material_array.append(0.6)
                if All_possible_profiles[j+1][6] == 'Recycled Construction steel S450':
                     material_array.append(0.8)
                if All_possible_profiles[j+1][6] == 'Duplex stainless steel 2205':
                     material_array.append(0.2)

                print('line '+str(j)+' added')
             
    plt.clf()

    xs = co2_array
    ys = price_array
    zs = number_array
    color = material_array
    counter = 0

    plt.scatter(xs,ys,c=color,cmap='viridis')
    plt.xlabel("Embodied carbon [kgCO₂e]",fontsize=16)
    plt.ylabel("price [€]",fontsize=16)

    plt.legend(
    handles=handles,
    title="Material Type",
    title_fontsize=14,   # Title font size
    fontsize=12,         # Font size of legend labels
    labelspacing=1.2     # Space between legend entries
    )

    for x,y,z in zip(xs,ys,zs):
        
        print(str(counter))
        counter = counter+1

        label = f"{z}"

        plt.annotate(label, # this is the text
                    (x,y), # these are the coordinates to position the label
                    textcoords="offset points", # how to position the text
                    xytext=(0,50), # distance from text to points (x,y)
                    ha='center') # horizontal alignment can be left, right or center
        

    plt.show()
    plt.savefig("excel_files/figure.png")

       #plot price and co2 function

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def plot_filtered_samples4(All_possible_profiles):
    
    co2_array = []
    price_array = []
    number_array = []
    material_array = []

    # Define the custom color map
    color_map = {
        0.0: '#00008B',  # dark blue
        0.4: '#ADD8E6',  # light blue
        0.6: '#006400',  # dark green
        0.8: '#90EE90',  # light green
        1.0: '#FFA500',  # orange
        0.2: '#800080'   # purple
    }

    # Material labels for legend
    material_labels = {
        0.0: 'Construction steel S355',
        0.4: 'Recycled Construction steel S355',
        1.0: 'Weathering steel S355',
        0.6: 'Construction steel S450',
        0.8: 'Recycled Construction steel S450',
        0.2: 'Duplex stainless steel 2205'
    }

    for j in range(len(All_possible_profiles)-1):
        co2_array.append(All_possible_profiles[j+1][9])
        price_array.append(All_possible_profiles[j+1][10])
        number_array.append(All_possible_profiles[j+1][0])

        mat = All_possible_profiles[j+1][6]
        if mat == 'construction steel S355':
            material_array.append(0.0)
        elif mat == 'Recycled Construction steel S355':
            material_array.append(0.4)
        elif mat == 'Weathering steel S355':
            material_array.append(1.0)
        elif mat == 'construction steel S450':
            material_array.append(0.6)
        elif mat == 'Recycled Construction steel S450':
            material_array.append(0.8)
        elif mat == 'Duplex stainless steel 2205':
            material_array.append(0.2)

        print('line '+str(j)+' added')

    plt.clf()

    xs = co2_array
    ys = price_array
    zs = number_array
    colors = [color_map[m] for m in material_array]

    plt.scatter(xs, ys, c=colors)
    plt.xlabel("Embodied carbon [kgCO₂e]", fontsize=50)
    plt.ylabel("Price [€]", fontsize=50)
    plt.xticks(fontsize=36)
    plt.yticks(fontsize=36)

    ax = plt.gca()  # get current axes

    # Format X and Y axes
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
    ax.ticklabel_format(style='sci', axis='x', scilimits=(0, 0))
    ax.xaxis.offsetText.set_fontsize(36)

    ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
    ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
    ax.yaxis.offsetText.set_fontsize(36)


    # Create custom legend
    legend_patches = [mpatches.Patch(color=color_map[key], label=material_labels[key]) for key in sorted(color_map.keys())]
    #plt.legend(handles=legend_patches, title="Coating Type", fontsize=42, title_fontsize=48,loc='upper left')


    for x, y, z in zip(xs, ys, zs):
        plt.annotate(
            f"{z}",
            (x, y),
            textcoords="offset points",
            xytext=(0, 10),
            ha='center'
        )

    plt.show()
    plt.savefig("excel_files/figure.png")


def plot_filtered_sampleszl(All_possible_profiles):
    
    co2_array = []
    price_array = []
    number_array = []
    material_array = []

    # Define the custom color map
    color_map = {
        0.0: '#00008B',  # dark blue
        0.4: '#ADD8E6',  # light blue
        0.6: '#006400',  # dark green
        0.8: '#90EE90',  # light green
        1.0: '#FFA500',  # orange
        0.2: '#800080'   # purple
    }

    # Material labels for legend
    material_labels = {
        0.4: 'Construction steel S355',
        0.0: 'Recycled Construction steel S355',
        1.0: 'Weathering steel S355',
        0.6: 'Construction steel S450',
        0.8: 'Recycled Construction steel S450',
        0.2: 'Duplex stainless steel 2205'
    }

    for j in range(len(All_possible_profiles)-1):
        co2_array.append(All_possible_profiles[j+1][9])
        price_array.append(All_possible_profiles[j+1][10])
        number_array.append(All_possible_profiles[j+1][0])

        mat = All_possible_profiles[j+1][6]
        if mat == 'construction steel S355':
            material_array.append(0.4)
        elif mat == 'Recycled Construction steel S355':
            material_array.append(0.0)
        elif mat == 'Weathering steel S355':
            material_array.append(1.0)
        elif mat == 'construction steel S450':
            material_array.append(0.6)
        elif mat == 'Recycled Construction steel S450':
            material_array.append(0.8)
        elif mat == 'Duplex stainless steel 2205':
            material_array.append(0.2)

        print('line '+str(j)+' added')

    plt.clf()

    xs = co2_array
    ys = price_array
    zs = number_array
    colors = [color_map[m] for m in material_array]

    plt.scatter(xs, ys, c=colors)
    plt.xlabel("Embodied carbon [kgCO₂e]", fontsize=48)
    plt.ylabel("Price [€]", fontsize=48)
    plt.xticks(fontsize=36)
    plt.yticks(fontsize=36)

    ax = plt.gca()  # get current axes

    # Format X and Y axes
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
    ax.ticklabel_format(style='sci', axis='x', scilimits=(0, 0))
    ax.xaxis.offsetText.set_fontsize(36)

    ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
    ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
    ax.yaxis.offsetText.set_fontsize(36)


    # Create custom legend
    legend_patches = [mpatches.Patch(color=color_map[key], label=material_labels[key]) for key in sorted(color_map.keys())]
    plt.legend(handles=legend_patches, title="Coating Type", fontsize=42, title_fontsize=48,loc='upper left')


    #for x, y, z in zip(xs, ys, zs):
    #    plt.annotate(
    #        f"{z}",
    #        (x, y),
    #        textcoords="offset points",
    #       xytext=(0, 50),
    #       ha='center'
    #    )

    plt.show()
    plt.savefig("excel_files/figure.png")

def plot_co2_price(All_possible_profiles):
    max_co2 = 0
    min_co2 = 100000000
    max_price = 0
    min_price = 100000000
    co2_array = []
    price_array = []
    number_array = []


    for i in range(len(All_possible_profiles)-1):
            if All_possible_profiles[i+1][9]>max_co2:
                max_co2 = All_possible_profiles[i+1][9]
            if All_possible_profiles[i+1][9]<min_co2:
                min_co2 = All_possible_profiles[i+1][9]       
            if All_possible_profiles[i+1][10]>max_price:
                max_price = All_possible_profiles[i+1][10]
            if All_possible_profiles[i+1][10]<min_price:
                min_price = All_possible_profiles[i+1][10]

            co2_array.append(All_possible_profiles[i+1][9])
            price_array.append(All_possible_profiles[i+1][10])
            number_array.append(All_possible_profiles[i+1][0])
    plt.clf()

    # using some dummy data for this example
    xs = co2_array
    ys = price_array
    zs = number_array

    plt.scatter(xs,ys)
    plt.xlabel("kg CO2e")
    plt.ylabel("price [euro]")

    for x,y,z in zip(xs,ys,zs):

        label = f"{z}"

        plt.annotate(label, # this is the text
                    (x,y), # these are the coordinates to position the label
                    textcoords="offset points", # how to position the text
                    xytext=(0,10), # distance from text to points (x,y)
                    ha='center') # horizontal alignment can be left, right or center
        plt.savefig("excel_files/figure.png")
    plt.show()


def plot_filtered_samplescoat(All_possible_profiles):
    
    co2_array = []
    price_array = []
    number_array = []
    material_array = []

    # Define the custom color map
    color_map = {
    0.0: '#0000FF',  # blue
    0.4: '#FF00FF',  # magenta
    0.6: '#FFA500',  # orange
    0.8: '#000000'   # black
    }

    # Material labels for legend
    material_labels = {
        0.0: 'Zinc primer',
        0.4: 'metalizing',
        
        0.6: 'Hot dip galvanizing',
        0.8: 'No coating',
        
    }

    for j in range(len(All_possible_profiles)-1):
        co2_array.append(All_possible_profiles[j+1][9])
        price_array.append(All_possible_profiles[j+1][10])
        number_array.append(All_possible_profiles[j+1][0])

        mat = All_possible_profiles[j+1][7]
        if mat == 'No coating':
            material_array.append(0.8)
        elif mat == 'Zinc_primer+paint':
            material_array.append(0.0)
        elif mat == 'Hot_dip_galvanizing+paint':
            material_array.append(0.6)
        elif mat == 'metalizing':
            material_array.append(0.4)
        

        print('line '+str(j)+' added')

    plt.clf()

    xs = co2_array
    ys = price_array
    zs = number_array
    colors = [color_map[m] for m in material_array]

    plt.scatter(xs, ys, c=colors, s=200)
    plt.xlabel("Embodied carbon [kgCO₂e]", fontsize=42)
    plt.ylabel("Price [€]", fontsize=42)
    plt.xticks(fontsize=36)
    plt.yticks(fontsize=36)

    ax = plt.gca()  # get current axes

    # Format X and Y axes
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
    ax.ticklabel_format(style='sci', axis='x', scilimits=(0, 0))
    ax.xaxis.offsetText.set_fontsize(40)

    ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
    ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
    ax.yaxis.offsetText.set_fontsize(40)


    # Create custom legend
    legend_patches = [mpatches.Patch(color=color_map[key], label=material_labels[key]) for key in sorted(color_map.keys())]
    plt.legend(handles=legend_patches, title="Coating Type", fontsize=46, title_fontsize=50,loc='upper left')

    for x, y, z in zip(xs, ys, zs):
        plt.annotate(
            f"{z}",
            (x, y),
            textcoords="offset points",
            xytext=(0, 10),
            ha='center',
            fontsize=28
        )

    plt.show()
    plt.savefig("excel_files/figure.png")
