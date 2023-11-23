import dendro.client as prc
from dendro.client._interim import NwbSorting
import remfile


# Load project {{ project.projectName }}
project = prc.load_project('{{ project.projectId }}')

# Lazy load {{ fileName }}
nwb_file = remfile.File(project.get_file('{{ fileName }}'))

# Create a recording object
sorting = NwbSorting(nwb_file)

# Get sorting information
unit_ids = sorting.get_unit_ids()
sampling_frequency = sorting.get_sampling_frequency()

print(f'Unit ids: {unit_ids}')
print(f'Sampling frequency (Hz): {sampling_frequency}')

spike_train_1 = sorting.get_unit_spike_train(unit_id=unit_ids[0])
print(f'Number of events for unit {unit_ids[0]}: {len(spike_train_1)}')
