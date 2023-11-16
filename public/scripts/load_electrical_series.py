import h5py
import dendro.client as prc
from dendro.client._interim import NwbRecording
import remfile


# Load project {{ project.projectName }}
project = prc.load_project('{{ project.projectId }}')

# Lazy load {{ fileName }}
nwb_file = remfile.File(project.get_file('{{ fileName }}'))
h5_file = h5py.File(nwb_file, 'r')

# Create a recording object
recording = NwbRecording(h5_file, electrical_series_path='{{ electricalSeriesPath }}')

# Get recording information
duration_sec = recording.get_duration()
sampling_frequency = recording.get_sampling_frequency()
num_channels = recording.get_num_channels()

print(f'Duration (sec): {duration_sec}')
print(f'Sampling frequency (Hz): {sampling_frequency}')
print(f'Number of channels: {num_channels}')

# Load the first 1000 frames of the recording
traces = recording.get_traces(start_frame=0, end_frame=1000)

print(f'Traces shape for first 1000 frames: {traces.shape}')
