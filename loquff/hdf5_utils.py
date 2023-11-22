import h5py

def delete_key(path,key):
    with h5py.File(path,  "a") as f:
        del f[key]

def show_keys(path):
    with h5py.File(path,  "r") as f:
        print(f.keys())

def get_image(path,key,index):
    with h5py.File(path,  "r") as f:
        return f[key][index,:,:]

def write_attrs(dest,keys,vals):
    for (key,val) in zip(keys,vals):
        dest.attrs[key] = val

def copy_attributes(dest,src):
    for attr in src.attrs:
        dest.attrs[attr] = src.attrs[attr]

def check_safety(file, saving_key):
    if saving_key in file.keys():
            raise Exception("There is already a dataset with the given name.")