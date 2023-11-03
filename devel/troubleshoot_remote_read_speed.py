import time
import h5py
import remfile

url = 'https://dandiarchive-embargo.s3.amazonaws.com/000620/blobs/8ce/bee/8cebeede-f6e8-4bd5-a307-ed3c852269bb?response-content-disposition=attachment%3B%20filename%3D%22sub-Elgar_ecephys.nwb%22&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAUBRWC5GAEKH3223E%2F20231101%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20231101T153921Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=0f41fc34bb4c1759489fca53c439359bfb450efac1f1780672c480a1d127569c'

# open the remote file
f = h5py.File(remfile.File(url, verbose=True), 'r')

# load the neurodata object
X = f['/acquisition/ElectricalSeriesAP']

starting_time = X['starting_time'][()]
rate = X['starting_time'].attrs['rate']
data = X['data']

print(f'starting_time: {starting_time}')
print(f'rate: {rate}')
print(f'data shape: {data.shape}')

timer = time.time()
x = data[:30000 * 60,0:10]
elapsed = time.time() - timer
print(f'elapsed (sec): {elapsed}')

print(x.shape)