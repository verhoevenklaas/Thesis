from Functions_k import *

from openpyxl import Workbook
import matplotlib.pyplot as plt
import numpy as np

#STEP 1: opening the .dat file and edit the h value
dat_file = r'C:\Users\verho\OneDrive\Current semester\Thesis\Sofistic\Model13\model_13.dat'

#height = list(range(500, 2600, 250))
height = [2500]
width = list(range(350,1300,150))
tw = [15,20,25]
tf = [30,35,40,45,50,55,60]


Steel_class = [355,450]
Steel_type = ['construction steel S355','Recycled Construction steel S355', 'Weathering steel S355','construction steel S450','Recycled Construction steel S450','Duplex stainless steel 2205']
Carbon_factor_steel = [1.740,0.567,1.740,1.740,0.567,3.8] # [kgCO_2e/kg] , HTEC table 2.3 (steel plates, no rolled profie possible for bridge girders)
Steel_price = [0.685,0.685,0.75,0.88,0.88,8.86] # Steel_price  #[euro/kg]

concrete_type = ['C40-50']
carbon_factor_concrete = [0.138] # [kgCO_2e/kg]
Concrete_price = [0.12] # concrete_price  #[euro/kg]

coating_type = ['Zinc_primer+paint','Hot_dip_galvanizing+paint','metalizing']
carbon_factor_coating = [1.45,11.1,13] # [kgCO_2e/m^2]
Coating_price = [6.2,2.6,43.1] # coating_price = #[euro/m^2]

L = 50

All_possible_profiles = [['profile index','Height','width','tw','tf','Steel class','Steel type','Coating type','Concrete type','KgCo2e','price (euro)']]
excel_index = 0
fc_max = 0

for k in range(len(Steel_class)):
        for j in range(len(width)):
                for i in range(len(height)):
                        for g in range(len(tw)):
                                for h in range(len(tf)):
                                        data = opening_dat_file(dat_file)
                                        data_edited = editing_cross_section_dat_file(data, height[i],width[j],tw[g],tf[h])
                                        data_edited = editing_steel_class_dat_file(data_edited,Steel_class[k])
                                        
                                
                                        dat_file_store = r'C:\Users\verho\OneDrive\Current semester\Thesis\Python\Dat_files_v2\Poject_file'+'_'+str(height[i])+'_'+str(width[j])+'_'+str(tw[g])+'_'+str(tf[h])+'_'+str(Steel_class[k])+'.dat'
                                        store_to_new_dat_file(data_edited, dat_file_store)

                                        #step 2: running the new .dat file
                                        running_dat_file(dat_file_store)

                                        #STEP 3: Connect to cdb file
                                        cdb_file = r'C:\Users\verho\OneDrive\Current semester\Thesis\Python\Dat_files_v2\Poject_file'+'_'+str(height[i])+'_'+str(width[j])+'_'+str(tw[g])+'_'+str(tf[h])+'_'+str(Steel_class[k])+'.cdb'
                                        myDLL, py_sof_cdb_get, py_sof_cdb_kenq, py_sof_cdb_kexist = get_the_DLLs_functions()
                                        Index = opening_cdb_file(cdb_file, myDLL)
                                        print(Index)


                                        #STEP 4: Reading some data from the database
                                        Med = Moment_beam_max(Index, py_sof_cdb_kexist, py_sof_cdb_get)
                                        print('Med =', Med, 'kNm')
                                        sig_c_max, sig_t_max = stresses_beam_max(Index, py_sof_cdb_kexist, py_sof_cdb_get)
                                        print('sig_c_1 =', sig_c_max, 'kPa')
                                        print('sig_t_1 =', sig_t_max, 'kPa')

                                        matnumber = 1
                                        if tf[h] > 40:
                                                matnumber = 6
                                        fyk,gam_s = fy_beam(Index, py_sof_cdb_kexist, py_sof_cdb_get,matnumber)
                                        fck,gam_c = fc_beam(Index, py_sof_cdb_kexist, py_sof_cdb_get)

                                        #temporary step for calculationg areas
                                        Area_profile_steel, Area_profile_concrete,Circumference_steel = beam_propertiestemp(data_edited)
                                        
                                        #step 5 checking if stresses are withing bounds

                                        check = CHECK_stresses(sig_c_max,sig_t_max,fyk,fck)


                                        #Step 6 calculating Co2 impact        
                                        if check == True:
                                                if sig_c_max<fc_max:
                                                        fc_max = sig_c_max

                                                weight_steel = gam_s*2*Area_profile_steel*L/9.81*1000 # [kg] convert from kN to kg
                                                weight_concrete = gam_c*Area_profile_concrete*L/9.81*1000 # [kg] convert from kN to kg
                                                Extrenal_area_steel = 2*Circumference_steel*L #[m^2] External area that needs coating in m^2
                                                #print('weight steel=', weight_steel, 'kg')
                                                #print('weight concrete=', weight_concrete, 'kg')
                                                if k==0:
                                                        steel_type_temp = [Steel_type[0],Steel_type[1],Steel_type[2]]
                                                        print(steel_type_temp)
                                                else:
                                                        steel_type_temp = [Steel_type[3],Steel_type[4],Steel_type[5]]  
                                                        print(steel_type_temp) 

                                                for l in range(len(steel_type_temp)):
                                                        for m in range(len(concrete_type)):
                                                                steelindex = k*3+l
                                                                Co2_steel = weight_steel*Carbon_factor_steel[steelindex] # [kgCO_2e]
                                                                price_steel = weight_steel*Steel_price[steelindex] # [euro]
                                                                Co2_concrete = weight_concrete*carbon_factor_concrete[m]
                                                                price_concrete = weight_concrete*Concrete_price[m]
                                                                if l<2:
                                                                        for n in range(len(coating_type)):
                                                                                price_coating = Coating_price[n]*Extrenal_area_steel
                                                                                Co2_coating = carbon_factor_coating[n]*Extrenal_area_steel
                                                                
                                                                                Total_co2 = Co2_steel+Co2_concrete+Co2_coating
                                                                                Total_price = price_steel+price_concrete+price_coating

                                                                                excel_index = excel_index+1
                                                                                profile_data = [excel_index,height[i],width[j],tw[g],tf[h],'S'+str(Steel_class[k]),steel_type_temp[l],coating_type[n],concrete_type[m],Total_co2,Total_price]
                                                                                All_possible_profiles.append(profile_data)
                                                                else:
                                                                        Total_co2 = Co2_steel+Co2_concrete
                                                                        Total_price = price_steel+price_concrete

                                                                        excel_index = excel_index+1
                                                                        profile_data = [excel_index,height[i],width[j],tw[g],tf[h],'S'+str(Steel_class[k]),steel_type_temp[l],'No coating',concrete_type[m],Total_co2,Total_price]
                                                                        All_possible_profiles.append(profile_data)


                        
                                        #STEP 7: Reading some data from the database
                                        closing_cdb_file(myDLL)




#STEP 8: write to excel file
write_excel_file(All_possible_profiles)
print('excel file stored')
print('max comp stress',fc_max)

#STEP 9: make a plot
#plot_co2_price(All_possible_profiles)


























