# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 16:19:23 2024

@author: julio
"""

from mcsmain import MCSh5
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import siunits as u
import pandas as pd

FRAMEBASE = 'Data/Recording_0/'
MCS_H5_DATASET_PATH = FRAMEBASE + 'AnalogStream/Stream_2/ChannelData'  
MCS_H5_INFO_PATH = FRAMEBASE + 'AnalogStream/Stream_2/InfoChannel'
#analog input data
Analog_Channel_Data = FRAMEBASE + 'AnalogStream/Stream_0/ChannelData'
Analog_Channel_Info = FRAMEBASE + 'AnalogStream/Stream_0/InfoChannel'

#Special datatype for info dataset
Acquisition_Info_Events_Base = FRAMEBASE + 'EventStream/Stream_0/'
Acquisition_Info_EventInfo=Acquisition_Info_Events_Base+"/InfoEvent"
Acquisition_Info_EventEntity=Acquisition_Info_Events_Base+"/EventEntity_0"

class Mea60_h5(MCSh5):
  def __init__(self, filepath, *args, **argv):
    
    super(Mea60_h5, self).__init__(filepath, *args, **argv)  
    #Update attributes. 
    self.update()
    self.update_analog()
  
  #Read methods inherited from MCSh5
  def update(self):
    self.data = self[MCS_H5_DATASET_PATH]
    self.info = self[MCS_H5_INFO_PATH]
    #Update calibration factors.
    #Datatype is 64 bit integer to be consistent with former dataformat.
    self.calib = np.array(self.info['ConversionFactor'][:-1],
                          dtype = np.int64)
    #Update framerate.
    self.framerate = 1000.0/self.info["Tick"][0] # Tick in us to framerate in kHz
    #electrodes, timestamps
    self.datashape = ((self.data.shape[0],
                       self.data.shape[1]))
    self.duration = self.data.shape[1] * self.info['Tick'][0]
    self.units = {"time":u.s*10**-6, "voltage": u.v*10**-6, "framerate":u.hz*10**3}
    return
  
  def update_analog(self):
    self.channels=pd.DataFrame()
    channels=self[Analog_Channel_Data]
    channellabels=self[Analog_Channel_Info]  
    array=[channels[i] for i in np.arange(channels.shape[0])]
    self.channels["signal"]=array
    self.channels["label"]=[el.decode() for el in channellabels["Label"]]
    self.channels["unit"]=[el.decode() for el in channellabels["Unit"]]
    self.channels["tick"]=channellabels["Tick"]
    self.channels["conversionFactor"]=channellabels["ConversionFactor"]
    self.channels["adcBits"]=channellabels["ADCBits"]
    self.channels["highPassFilterType"]=[el.decode() for el in channellabels["HighPassFilterType"]]
    self.channels["highPassFilterCutOffFrequency"]=channellabels["HighPassFilterCutOffFrequency"]
    self.channels["highPassFilterOrder"]=channellabels["HighPassFilterOrder"]               
    self.channels["lowPassFilterType"]=[el.decode() for el in channellabels["LowPassFilterType"]]
    self.channels["lowPassFilterCutOffFrequency"]=channellabels["LowPassFilterCutOffFrequency"]
    self.channels["lowPassFilterOrder"]=channellabels["LowPassFilterOrder"]   
    return  
  
  def get_data(self):
    return self.data[:,:]

  
  
  def set_data(self, data, append = False):
    #Set whole dataset to data or append data to already existing dataset.
    #Input data in electrodes x frames.
    #Delete old dataset and set new entries.
    view = data
    try:
      if append:
        self[MCS_H5_DATASET_PATH].resize((self.data.shape[0] , \
                                          self.data.shape[1]+ view.shape[1]))
        self[MCS_H5_DATASET_PATH][:,-view.shape[1]:] = view[:,:]
      else:
        if view.shape != self[MCS_H5_DATASET_PATH].shape:
          self[MCS_H5_DATASET_PATH].resize(view.shape)
        self[MCS_H5_DATASET_PATH][:,:] = view[:,:]
    except:
      #Dataset does not yet exist.
      #Maybe use reshape functionality of h5py by giving maxshape.
      #Not sure if this would give a performance boost compared to recreation.
      print("dataset does not exist yet.")
      
    finally:
      self.update()
    return
  
  
  def dateticks(self):
    #Tool to calculate the c# equivalent to DateTime.Ticks property.
    #Current UTC time in ticks of .1 micro seconds since 01.01.0001 00:00 
    return (datetime.utcnow() - datetime(1, 1, 1)).total_seconds() * 1e7

  def plot_raw_trace(self, electrode, xlim=[0,50000]):
    data=self.get_data()[electrode]
    t=np.linspace(0,self.duration, num= data.shape[0])/1000000
    plt.plot(t,data)
    xlim = [0, t[-1]]
    plt.xlim(xlim)
    plt.xlabel("time (s)")
    plt.ylabel("voltage [%s]"%self.units["voltage"])
    plt.show()
  
  def plot_analog(self):#, xlim=[0,100000]):
      #fig, axs = plt.subplots(4,1)
      #xlim=[0,10000]
      #ylim=[-32765, -32768]
      
      ch = self.channels.index[0]
      y=self.channels["signal"][ch]
      y[y == -32768] = 0
      y[y == -32767] = 1
      x=np.arange(0, self.channels["tick"][ch]*len(y), self.channels["tick"][ch])/1000000
      
      plt.step(x,y)
      plt.xlabel("time (s)")
      plt.title('Analogic Data')
    
      plt.show()
          
  def get_trigger(self):
      ch = self.channels.index[0]
      y=self.channels["signal"][ch]
      x=np.arange(0, self.channels["tick"][ch]*len(y), self.channels["tick"][ch])
      
      return x, y