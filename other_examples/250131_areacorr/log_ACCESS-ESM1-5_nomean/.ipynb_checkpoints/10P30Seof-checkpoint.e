/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/distributed/client.py:3362: UserWarning: Sending large graph of size 192.15 MiB.
This may cause some slowdown.
Consider loading the data with Dask directly
 or using futures or delayed objects to embed the data into the graph without repetition.
See also https://docs.dask.org/en/stable/best-practices.html#load-data-with-dask for more information.
  warnings.warn(
/glade/u/home/jjeffree/ensemble-analogue-predictability/eof_calculation.py:53: UserWarning: Model data aquired; ACCESS-ESM1-5_nomean; 10.029250860214233 s
  warnings.warn('Model data aquired; '+data_name+"; "+str(time.time()-t0)+' s')
/glade/u/home/jjeffree/ensemble-analogue-predictability/eof_calculation.py:56: UserWarning: Calculating 10P30S
  warnings.warn('Calculating '+mask)
Traceback (most recent call last):
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/xarray/backends/file_manager.py", line 211, in _acquire_with_cache_info
    file = self._cache[self._key]
           ~~~~~~~~~~~^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/xarray/backends/lru_cache.py", line 56, in __getitem__
    value = self._cache[key]
            ~~~~~~~~~~~^^^^^
KeyError: [<class 'netCDF4._netCDF4.Dataset'>, ('/glade/derecho/scratch/jjeffree/pca_variations/area_correlation_weight/ACCESS-ESM1-5_nomean_I1_NINO34_L0/weights.nc',), 'r', (('clobber', True), ('diskless', False), ('format', 'NETCDF4'), ('persist', False)), 'b55cd9bd-cf66-4764-a219-82cf730c0bc9']

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/glade/u/home/jjeffree/ensemble-analogue-predictability/eof_calculation.py", line 66, in <module>
    weights = xr.load_dataarray(weightfolder_name+'weights.nc')
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/xarray/backends/api.py", line 303, in load_dataarray
    with open_dataarray(filename_or_obj, **kwargs) as da:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/xarray/backends/api.py", line 769, in open_dataarray
    dataset = open_dataset(
              ^^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/xarray/backends/api.py", line 588, in open_dataset
    backend_ds = backend.open_dataset(
                 ^^^^^^^^^^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/xarray/backends/netCDF4_.py", line 645, in open_dataset
    store = NetCDF4DataStore.open(
            ^^^^^^^^^^^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/xarray/backends/netCDF4_.py", line 408, in open
    return cls(manager, group=group, mode=mode, lock=lock, autoclose=autoclose)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/xarray/backends/netCDF4_.py", line 355, in __init__
    self.format = self.ds.data_model
                  ^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/xarray/backends/netCDF4_.py", line 417, in ds
    return self._acquire()
           ^^^^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/xarray/backends/netCDF4_.py", line 411, in _acquire
    with self._manager.acquire_context(needs_lock) as root:
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/contextlib.py", line 137, in __enter__
    return next(self.gen)
           ^^^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/xarray/backends/file_manager.py", line 199, in acquire_context
    file, cached = self._acquire_with_cache_info(needs_lock)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/xarray/backends/file_manager.py", line 217, in _acquire_with_cache_info
    file = self._opener(*self._args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "src/netCDF4/_netCDF4.pyx", line 2470, in netCDF4._netCDF4.Dataset.__init__
  File "src/netCDF4/_netCDF4.pyx", line 2107, in netCDF4._netCDF4._ensure_nc_success
FileNotFoundError: [Errno 2] No such file or directory: '/glade/derecho/scratch/jjeffree/pca_variations/area_correlation_weight/ACCESS-ESM1-5_nomean_I1_NINO34_L0/weights.nc'
