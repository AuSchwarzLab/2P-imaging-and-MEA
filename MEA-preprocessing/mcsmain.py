# -*- coding: utf-8 -*-
"""
Class handling different types of mcs-h5 files.
Created on Fri Oct 13 08:52:14 2017

@author: FlorianJ
"""
__version__ = "0.0"
#OPEN ISSUE:
#AUTOMATIC RECOGNITION OF h5-DATATYPE OF EXISTING FILES 
import numpy as np
import h5py
from os.path import exists

class MCSh5(h5py.File):
  #Inherit h5 class functions and attributes.
  def __init__(self, filepath,*args, **argv):
    self.filepath = filepath
    # Create some useful proxy's to attributes of the HDF5 File
    if not exists(self.filepath):
      h5py.File.__init__(self, filepath, *args, **argv)
      self.set_default(argv)
    else:
      h5py.File.__init__(self, filepath, *args, **argv)
    return 
  def update(self):
    print('Included in subclasses.')
    return
  def update_guid(self):
    print('Not available for non CMOS-MEA files.')
    return
  
  def get_data(self):
    return self.data[:,:,:]
  
  def get_calib(self):
    return self.calib
  
  def get_calibrated_data(self):
    #Returns data in V.
    #IMPORTANT: DIFFERENT FROM self.data[:,:,:] * self.calib[:,:,np.newaxis]!
    #CLASSIC h5-FILES MIGHT NEED TO TRANSPOSE CALIB!
    #ALREADY IMPLEMENTED IN classic_h5 read_calib.
    return self.get_data() * self.get_calib()[:,:,np.newaxis] * 1.e-9
  
  def set_default(self):
    print('Do stuff')
    return
