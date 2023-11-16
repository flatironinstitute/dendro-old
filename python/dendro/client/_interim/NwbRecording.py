# type: ignore

from typing import Union, List
import numpy as np
import h5py
import spikeinterface as si


class NwbRecording(si.BaseRecording):
    def __init__(self,
        file: h5py.File,
        electrical_series_path: str
    ) -> None:
        electrical_series: h5py.Group = file[electrical_series_path]
        electrical_series_data = electrical_series['data']
        dtype = electrical_series_data.dtype

        # Get sampling frequency
        if 'starting_time' in electrical_series.keys():
            # t_start = electrical_series['starting_time'][()]
            sampling_frequency = electrical_series['starting_time'].attrs['rate']
        elif 'timestamps' in electrical_series.keys():
            # t_start = electrical_series['timestamps'][0]
            sampling_frequency = 1 / np.median(np.diff(electrical_series['timestamps'][:1000]))

        # Get channel ids
        electrode_indices = electrical_series['electrodes'][:]
        electrodes_table = file['/general/extracellular_ephys/electrodes']
        channel_ids = [electrodes_table['id'][i] for i in electrode_indices]

        si.BaseRecording.__init__(self, channel_ids=channel_ids, sampling_frequency=sampling_frequency, dtype=dtype)

        # Set electrode locations
        if 'x' in electrodes_table:
            channel_loc_x = [electrodes_table['x'][i] for i in electrode_indices]
            channel_loc_y = [electrodes_table['y'][i] for i in electrode_indices]
            if 'z' in electrodes_table:
                channel_loc_z = [electrodes_table['z'][i] for i in electrode_indices]
            else:
                channel_loc_z = None
        elif 'rel_x' in electrodes_table:
            channel_loc_x = [electrodes_table['rel_x'][i] for i in electrode_indices]
            channel_loc_y = [electrodes_table['rel_y'][i] for i in electrode_indices]
            if 'rel_z' in electrodes_table:
                channel_loc_z = [electrodes_table['rel_z'][i] for i in electrode_indices]
            else:
                channel_loc_z = None
        else:
            channel_loc_x = None
            channel_loc_y = None
            channel_loc_z = None
        if channel_loc_x is not None:
            ndim = 2 if channel_loc_z is None else 3
            locations = np.zeros((len(electrode_indices), ndim), dtype=float)
            for i, electrode_index in enumerate(electrode_indices):
                locations[i, 0] = channel_loc_x[electrode_index]
                locations[i, 1] = channel_loc_y[electrode_index]
                if channel_loc_z is not None:
                    locations[i, 2] = channel_loc_z[electrode_index]
            self.set_dummy_probe_from_locations(locations)

        # Extractors channel groups must be integers, but Nwb electrodes group_name can be strings
        if "group_name" in electrodes_table:
            unique_electrode_group_names = list(np.unique(electrodes_table["group_name"][:]))

            groups = []
            for electrode_index in electrode_indices:
                group_name = electrodes_table["group_name"][electrode_index]
                group_id = unique_electrode_group_names.index(group_name)
                groups.append(group_id)
            self.set_channel_groups(groups)

        recording_segment = NwbRecordingSegment(
            electrical_series_data=electrical_series_data,
            sampling_frequency=sampling_frequency
        )
        self.add_recording_segment(recording_segment)

class NwbRecordingSegment(si.BaseRecordingSegment):
    def __init__(self, electrical_series_data: h5py.Dataset, sampling_frequency: float) -> None:
        self._electrical_series_data = electrical_series_data
        si.BaseRecordingSegment.__init__(self, sampling_frequency=sampling_frequency)

    def get_num_samples(self) -> int:
        return self._electrical_series_data.shape[0]

    def get_traces(self, start_frame: int, end_frame: int, channel_indices: Union[List[int], None] = None) -> np.ndarray:
        if channel_indices is None:
            return self._electrical_series_data[start_frame:end_frame, :]
        else:
            return self._electrical_series_data[start_frame:end_frame, channel_indices]
