# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:24:13 2024

@author: PierreA.DERRIEN
"""

import sys
import os
import pathlib
import traceback
import logging
from datetime import datetime

#  Get the file directory to find all the parent submmodule whereever the user put this script
script_directory = pathlib.Path(__file__).parent.resolve()
file_path = str(script_directory).split("\\")[:-3]
file_path[0] = file_path[0]+r"\\"
module_folder = os.path.join(*file_path)
sys.path.append(module_folder)


from NWB.Fiberphotometry_builder.convert_from_excel import convert_excel_to_nwb
from NWB.General_tools import PySimpleGUI as sg

# All the stuff inside your window.
layout = [[sg.Text('Enter the Excel file to setup the conversion tool')],
          [sg.Text('File', size=(8, 1)), sg.Input(), sg.FileBrowse()],
          [sg.Submit(), sg.Cancel()]] 

# Create the Window
window = sg.Window('GUI converter', layout)

# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    
    if event == "Submit":
        try:
            # Check if the input file is from the GitHub repo
            repo_path = os.path.abspath(os.path.join(script_directory, "..", "..", ".."))
            input_path = os.path.abspath(values[0])
            
            if input_path.startswith(repo_path):
                sg.popup_error("Please don't use the Setup_NWB.xlsx from the GitHub repository.\n"
                             "Copy it to your data folder first.")
                continue
                
            # Setup logging
            path_list = values[0].split("/")[:-1]
            path_list[0] = path_list[0]+r"\\"
            direc_path = os.path.join(*path_list)
            log_path = os.path.join(direc_path, "Files", "log.txt")
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_path),
                    logging.StreamHandler()
                ]
            )
            logger = logging.getLogger(__name__)
            
            # Log initial information
            logger.info("="*50)
            logger.info(f"Conversion started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Setup file path: {values[0]}")
            logger.info(f"Output directory: {os.path.join(direc_path, 'Files')}")
            logger.info("="*50)
            
            
            
            logger.info(f"Working directory: {os.path.join(direc_path, 'Files')}")
            
            if os.path.exists(os.path.join(direc_path, "Files")) == False: 
                logger.info("No files directory, making one")
                os.mkdir(os.path.join(direc_path, "Files"))
            else: 
                logger.info("Files directory already exists")
                
            convert_excel_to_nwb(values[0], os.path.join(direc_path, "Files"), logger=logger)
            logger.info("Conversion completed successfully")
            
        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            logger.error(traceback.format_exc())
            sg.popup_scrolled("Error : "+str(e))
            traceback.print_exc()
        
    # if user closes window or clicks cancel
    if event == sg.WIN_CLOSED or event == 'Cancel':
        break
window.close()



