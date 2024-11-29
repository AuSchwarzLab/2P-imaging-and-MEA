# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 16:32:12 2024

@author: julio
"""

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
plt.figure()
plt.close()

import numpy as np
import os
import pandas as pd
import sys, inspect
import siunits as u
import pickle
from scipy import stats as st


from circus.shared.parser import CircusParser
from circus.shared.files import load_data, get_stas
from circus.shared.probes import get_nodes_and_edges

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
import mea60_h5 as MEA60
sys.path.remove(parentdir)


class MEA_spykingCircus():
    def __init__(self, filename, *args, align_waveforms=True, **argv):
        print("\n MEA_spykingCircus init: %s"%filename)
        params    = CircusParser(filename)
        self.filename=filename
        meafile=MEA60.Mea60_h5(self.filename, "r")
        
        self.meafile = meafile
        self.params=params
        
        
    
    def get_time_vector(self):
        x,y = self.meafile.get_trigger()
        stimuli_duration = self.meafile.duration/1000000
        time_vector = np.linspace(0, stimuli_duration, len(y))
        change_indices_analog = np.where(y[:-1] != y[1:])[0] +1
        #first_cond_change = time_vector[change_indices_analog[0]]
        time_cond_changes = []
        
        for index in change_indices_analog:
             time_cond_change= time_vector[index]
             time_cond_changes.append(time_cond_change)
             
        time_cond_changes_from_start = np.insert(time_cond_changes, 0,0)
        time_differences = np.zeros_like(time_cond_changes_from_start)
        
        for i in range(1, len(time_cond_changes_from_start)):
             time_differences[i] = time_cond_changes_from_start [i] - time_cond_changes_from_start[i - 1]
             
        time_differences = np.delete(time_differences, 0)

        time_differences_cond1 = time_differences[::2]
        time_differences_cond2 = time_differences[1::2]

        last_duration = stimuli_duration-time_cond_changes[-1]

        time_differences_cond2 = np.append(time_differences_cond2, last_duration)

        differences_time = {'cond1': time_differences_cond1, 'cond2': time_differences_cond2}
        
        return  differences_time, time_cond_changes
        
        
        
    def get_trials(self):
        # Load results
        results = load_data(self.params, 'results')
    
        # Extract and scale spike times
        #samplingrate=self.params.rate
        samplingrate = self.meafile.framerate*1000
        
        spike_times = [
            np.array(results['spiketimes'][f'temp_{i}']) / samplingrate
            for i in range(len(results["spiketimes"]))
        ]
    
        # Extract trigger data and identify transition points
        x, y = self.meafile.get_trigger()
        pos1, pos2 = min(y), max(y)
        change_indices_analog = np.where((y[:-1] == pos1) & (y[1:] == pos2))[0] + 1
    
        x_spont = x[0:change_indices_analog[0]]
        x_event_related = x[change_indices_analog[0]:]/1000000
        
        #y_spont = y[0:change_indices_analog[0]]
        y_event_related = y[change_indices_analog[0]:]
        
        change_indices_event = np.where((y_event_related[:-1] == pos1) & (y_event_related[1:] == pos2))[0] +1
        
        spont_index = x_spont[-1]/1000000
        
        #event_indexes = change_indices_analog [1:]
        
        spont_activity = []
        event_related_activity = []

        for time_stamps in spike_times:
            current_trial_spont = []
            current_trial_event_related = []
            for value in time_stamps:
                if value <= spont_index:
                    current_trial_spont.append(value)
                else:
                    current_trial_event_related.append(value)
                    #break
            spont_activity.append(current_trial_spont)
            event_related_activity.append(current_trial_event_related)
            
            
        time_cond_changes = []
         
        for index in change_indices_event:
             time_cond_change= x_event_related[index]
             time_cond_changes.append(time_cond_change)
        
            
        trials_event_related = []
        for sublist in event_related_activity:
            sublists = []
            current_index = spont_index
            for i, time_change in enumerate(time_cond_changes):
                values_in_range = [value - current_index for value in sublist if current_index <= value < time_change]
                sublists.append(np.array(values_in_range))
                current_index = time_change
            
            values_in_range = [value - current_index for value in sublist if value >= current_index]
            sublists.append(np.array(values_in_range))
            trials_event_related.append(sublists)
        
        return trials_event_related
    
    
    
    def compute_OOindex(self, templateid):
        x,y = self.meafile.get_trigger()
        
        trials = self.get_trials()
        #trials = trials_data['trials_event_related']
        
        trial = trials[templateid][:-1]
        
        time_changes, time_durs = self.get_time_vector()
        mode_cond1 = st.mode(time_changes['cond1'])
        mode_cond2 = st.mode(time_changes['cond2'])
        max_value = int(np.round(mode_cond1.mode)+np.round(mode_cond2.mode))

        if(y[0]==min(y)):
            light_on = 0
            light_off = max_value/2
            
            onset_time = light_on
            offset_time = light_off
            dur_stim = light_off
        else:
        
            light_on = max_value/2
            light_off = max_value
            
            onset_time = light_on
            offset_time = light_off
            dur_stim = light_off - light_on
            
            
        average_onset_rates = []
        average_offset_rates = []
        
        for i in range(len(trial)):
            trial_spikes = trial[i]
            
            if(y[0]==min(y)):
                onset_spikes = [spike for spike in trial_spikes if spike >= onset_time and spike < offset_time]
                offset_spikes = [spike for spike in trial_spikes if spike >= offset_time]
            else:
                offset_spikes = [spike for spike in trial_spikes if spike >= 0 and spike < onset_time]
                onset_spikes = [spike for spike in trial_spikes if spike >= onset_time]
            
            
            
            onset_spike_count = len(onset_spikes)
            offset_spike_count = len(offset_spikes)
            
            onset_spike_rate = onset_spike_count / dur_stim
            offset_spike_rate = offset_spike_count / dur_stim
            
            average_onset_rates.append(onset_spike_rate)
            average_offset_rates.append(offset_spike_rate)
        
        
        average_onset_rate = np.mean(average_onset_rates)
        average_offset_rate = np.mean(average_offset_rates)
    
        
        OOi = (average_onset_rate-average_offset_rate)/(average_onset_rate+average_offset_rate)
        OOi = round(OOi,2)   
        
        return OOi