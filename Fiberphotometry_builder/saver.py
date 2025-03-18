# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 15:18:05 2024

@author: PierreA.DERRIEN
"""

import os
from pathlib import Path
from pynwb import NWBHDF5IO
import platform

def validate_save_path(filepath):
    """Validate and prepare the save path for both Windows and macOS."""
    # Convert to Path object
    save_path = Path(filepath)
    
    # Create parent directories if they don't exist
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check platform-specific constraints
    if platform.system() == 'Windows':
        # Check Windows path length limitation
        if len(str(save_path)) > 260:
            raise OSError(f"File path exceeds Windows maximum path length: {save_path}")
    
    return save_path

def save_NWB(NWB_file, filepath, export=False):
    """
    Save NWB file with cross-platform compatibility.
    
    Parameters:
    -----------
    NWB_file : NWBFile
        The NWB file object to save
    filepath : str or Path
        The path where to save the file (without extension)
    export : bool, optional
        Whether to export the file (default: False)
    """
    try:
        # Validate and prepare save path
        save_path = validate_save_path(filepath)
        
        # Add .nwb extension
        save_path = save_path.with_suffix('.nwb')
        
        if not export:
            with NWBHDF5IO(str(save_path), 'w') as io:
                io.write(NWB_file)
        else:
            with NWBHDF5IO(str(save_path), mode="r") as read_io:    
                read_nwbfile = read_io.read()
                with NWBHDF5IO(str(save_path), mode="w") as export_io:
                    export_io.export(src_io=read_io, nwbfile=read_nwbfile)
                    
    except Exception as e:
        raise IOError(f"Failed to save NWB file: {str(e)}")