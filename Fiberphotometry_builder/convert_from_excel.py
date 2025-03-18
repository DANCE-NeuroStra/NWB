# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 15:25:15 2024

@author: PierreA.DERRIEN
"""

from .builder_photometry import create_NWB
from .saver import save_NWB
from .file_openers.doric_system_file import DoricCSV, DoricDORIC
from .file_openers.labview_system_file import LVM_1segments

import pandas as pd
import os
from uuid import uuid4
from alive_progress import alive_bar
import logging
from pathlib import Path  # More modern path handling

def convert_gen_info(info):
    
    """ Input : pd.Dataframe
        Return: Dict
    """
    formated_info = {}
    item_list = ["session_description","session_id","notes",
                 "protocol","lab","institution","experiment_description",
                 "related_publications", "virus","surgery","pharmacology"]
    
    for item in item_list:
        try:
            formated_info[item]=info[info["General Info"]==item]["Unnamed: 1"].tolist()[0]
        except IndexError:
            # print(item)
            formated_info[item]= "None"
    formated_info["identifier"]=str(uuid4())
    formated_info["experimenter"] = info["Experimenters"].dropna().tolist()
    formated_info["keywords"]= info["Keywords"].dropna().tolist()
    formated_info["source_script"] ="Script file used to create this NWB file"# optional
    formated_info["source_script_file_name"]="Name of the source_script file"# optional
    return formated_info

def retrieve_animal(info):
    """ Input: pd.Series
        Return: dict
    """
    formated = {}
    # Change default date to indicate it's unidentified/placeholder
    session_start = datetime(1900, 1, 1, 0, 0, 0, tzinfo=tz.gettz("US/Pacific"))  # Unidentified date
    for i in info.index:
        if i == "File Directory" :
            file_direc = info[i]
        elif i == "session_start_time":
            try:
                session_start = pd.to_datetime(info[i])
            except ValueError:
                print(f"Invalid date format for session_start_time: {info[i]}")
                session_start = datetime(1900, 1, 1, 0, 0, 0, tzinfo=tz.gettz("US/Pacific"))  # Unidentified date
        elif i== "File_name":     
            file_name = info[i]
        elif i =="Animal number" or i=="Comments":
            pass
        elif i != "date_of_birth":    
            formated[i]= str(info[i])
        else:
            formated[i]= info[i]
    filepath = os.path.join(file_direc, file_name)
    
    return session_start, formated , filepath

def convert_channel_info(info):
    Fibers_dict = {}
    for col in info.columns:
        Fiber_Signals_info = {"imaging rate": info[col][" | Imaging rate"],
                              "indicator": info[col][" | indicator"],
                              "location": info[col][" | location"],
                              "coordinate": (info[col][" | AP"], info[col][" | ML"], info[col][" | DV"]),
                              "fiber diameter": info[col][" | Fiber diameter"], 
                              "fiber NA": info[col][" | fiber NA"],
                            }
        Signals = {}
        for n in range(int(info[col][" | Signals n"])):
            n +=1
            if "Isobestic" in info[col]["Signal "+str(n)+" | Name"]:
                Signal_dict = {"excitation":info[col]["Signal "+str(n)+" | excitation"], 
                                "emission":info[col]["Signal "+str(n)+" | emission"],
                                "data": {"raw_iso":info[col]["Signal "+str(n)+" | raw signal"],
                                        "demodulated_iso":info[col]["Signal "+str(n)+" | demodulated"],
                                }}
                Signals[info[col]["Signal "+str(n)+" | Name"]]=Signal_dict
            else:
                Signal_dict = {"excitation":info[col]["Signal "+str(n)+" | excitation"], 
                               "emission":info[col]["Signal "+str(n)+" | emission"],
                               "data": {"raw_signal":info[col]["Signal "+str(n)+" | raw signal"],
                                        "demodulated_signal":info[col]["Signal "+str(n)+" | demodulated"],
                                }}
                Signals[info[col]["Signal "+str(n)+" | Name"]]=Signal_dict
        Fiber_Signals_info["signals"] = Signals
            
        Fibers_dict[info[col][" | Fiber name"]]= Fiber_Signals_info
    return Fibers_dict
    
def convert_device(device_info):
    info = {"Name": device_info["Name"][0], 
            "Description": device_info["Description"][0],
            "Manufacturer": device_info["Manufacturer"][0]}
    return info


def convert_TTL (info):
    
    TTL_dict = {}
    for col in info.columns[1:]:
        TTL = {"data":info[info["Infos"]== "data"][col].tolist()[0],
               "description":info[info["Infos"]== "description"][col].tolist()[0]
                   }
        TTL_dict[info[info["Infos"]== "TTL_name"][col].tolist()[0]] = TTL
    return TTL_dict

def get_opener(filepath):
    # Use Path for better cross-platform compatibility
    extension = Path(filepath).suffix.lower()[1:]  # removes the dot and converts to lowercase
    print(f"Extension detected: {extension}")
    if extension == "csv":
        print("CSV file opener")
        return DoricCSV()
    elif extension == "doric":
        print("DORIC file opener")
        return DoricDORIC()
    elif extension == "lvm":
        print("LVM file opener")
        return LVM_1segments()
    

import warnings
from datetime import datetime
from dateutil import tz

def convert_excel_to_nwb(file, save_direc, warning =  False, logger = None):
    """
    

    Parameters
    ----------
    file : TYPE
        DESCRIPTION.
    save_direc : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    logging.basicConfig(level= logging.INFO)
    log = logging.getLogger('alive_progress')
    
    # Convert input paths to Path objects
    file = Path(file)
    save_direc = Path(save_direc)
    
    # Ensure save directory exists
    save_direc.mkdir(parents=True, exist_ok=True)
    
    if warning == False:
        warnings.filterwarnings("ignore")
    print("\n Start script")
    general_info = pd.read_excel(file, sheet_name="General_info")
    animals_info = pd.read_excel(file, sheet_name="Animals_info", skiprows=1)
    channel_info = pd.read_excel(file, sheet_name="Fiberphotometry_signals", skiprows=0)
    device_info = pd.read_excel(file, sheet_name="Device_info")
    TTL_info = pd.read_excel(file, sheet_name="TTL_info").dropna(axis = 1)
    print("\n All info loaded from excel")
    convertedTTL = convert_TTL(TTL_info)
    device_info = convert_device(device_info)
    
    # channel_info[channel_info.columns[0]].fillna(method= "ffill", inplace = True)
    # channel_info[channel_info.columns[0]].fillna("", inplace = True)
    
    channel_info[channel_info.columns[0]].ffill(inplace = True)
    channel_info[channel_info.columns[0]].fillna("", inplace = True)
    
    channel_info[channel_info.columns[1]] = channel_info[channel_info.columns[0]] +" | "+ channel_info[channel_info.columns[1]]
    channel_info = channel_info[channel_info.columns[1:]]
    channel_info.set_index(channel_info.columns[0], inplace = True)
    converted_gen_info = convert_gen_info(general_info)
    # converted_channel_info = convert_channel_info(channel_info)
    print("\n Start file conversion to NWB")
    # with MoonSpinner('Processing…') as bar:
    with alive_bar(len(animals_info)) as bar:
        for index, row in animals_info.iterrows():
            multi_anim = True
            try: 
                # We assume that multi animal is here
                if len(animals_info["Animal number"].unique())==1:
                    if str(animals_info["Animal number"].unique()[0]) =='nan' :   
                        converted_channel_info = convert_channel_info(channel_info)
                        multi_anim = False
                        
                if multi_anim:
                    col_to_keep = []
                    for col in channel_info.columns:
                        if channel_info.at[' | Animal number',col]==row["Animal number"]:
                            col_to_keep.append(col)
                    converted_channel_info = convert_channel_info(channel_info[col_to_keep])
                session_start, anim ,filepath = retrieve_animal(row)
                print(session_start)
        # =============================================================================
        #         auto opener in function of extension
        # =============================================================================
                converted_gen_info["session_start_time"] = session_start
                logger.info(f"File used for conversion: {filepath}")
                opener = get_opener(filepath)
                opener.open_file(filepath)
            
                print("File openned")
                File = create_NWB(converted_gen_info, anim,{"Device":device_info, "channels":converted_channel_info}, opener.data, convertedTTL)
                # Format the session start time
                session_start_str = str(session_start).replace(" ", "_").replace(":", "-")
                
                # Build the save path
                save_path_parts = [
                    row['subject_id'],
                    session_start_str
                ]
                
                if pd.notna(row['Animal number']) and row['Animal number'] != '' and row['Animal number'] is not None:
                    save_path_parts.append(str(row['Animal number']))
                
                if pd.notna(row['Comments']) and row['Comments'] != '' and row['Comments'] is not None:
                    save_path_parts.append(str(row['Comments']).replace(" ", "_"))
                
                # Use Path for building save paths
                save_path = save_direc.joinpath("_".join(save_path_parts))
                print(f"File saving to: {save_path}")
                save_NWB(File, save_path)   
                logger.info(f"File saved at: {save_path}")
            except KeyError as e:
                print("------------------------------------------------------")
                print("Error in file: {0}".format(filepath))
                if e in ["subject_id","session_start_time","Animal number", "Comments"]:
                    print("One or more of the Animal Info are incorrect")
                    print("The avalaible columns in the data are:")
                    for col in animals_info.columns:
                        print(col)
                    print("but should be: subject_id, session_start_time, Animal number, Comments")
                else:
                    print(f"Key error in the channel info: {e}")
                    print("One or more of the Channel Name are incorrect")
                    print("The avalaible channel in the data are:")
                    for col in opener.data:
                        print(col)
                    print("------------------------------------------------------")
                logger.error(f"Error in file: {filepath}")
                if e in ["subject_id", "session_start_time", "Animal number", "Comments"]:
                    logger.error("One or more of the Animal Info are incorrect")
                    logger.error("The available columns in the data are:")
                    for col in animals_info.columns:
                        logger.error(col)
                    logger.error("but should be: subject_id, session_start_time, Animal number, Comments")
                else:
                    logger.error(f"Key error in the channel info: {e}")
                    logger.error("One or more of the Channel Name are incorrect")
                    logger.error("The available channels in the data are:")
                    for col in opener.data:
                        logger.error(col)
                    logger.error("------------------------------------------------------")
            except Exception as e:
                print(e)
                logger.error(f"Error in file: {filepath}")
                logger.error(e)
                logger.error("------------------------------------------------------")
            bar()
            # break
    print("\ End file conversion to NWB")
    logger.info("End file conversion to NWB")