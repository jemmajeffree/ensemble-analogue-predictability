/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/distributed/client.py:3362: UserWarning: Sending large graph of size 192.15 MiB.
This may cause some slowdown.
Consider loading the data with Dask directly
 or using futures or delayed objects to embed the data into the graph without repetition.
See also https://docs.dask.org/en/stable/best-practices.html#load-data-with-dask for more information.
  warnings.warn(
/glade/u/home/jjeffree/ensemble-analogue-predictability/eof_calculation.py:53: UserWarning: Model data aquired; ACCESS-ESM1-5_nomean; 8.434184551239014 s
  warnings.warn('Model data aquired; '+data_name+"; "+str(time.time()-t0)+' s')
/glade/u/home/jjeffree/ensemble-analogue-predictability/eof_calculation.py:56: UserWarning: Calculating 10P30N
  warnings.warn('Calculating '+mask)
Traceback (most recent call last):
  File "/glade/u/home/jjeffree/ensemble-analogue-predictability/eof_calculation.py", line 63, in <module>
    masked_model_ss = month_model_ss.where(pt.mask_dict[mask],drop=True)
                                           ~~~~~~~~~~~~^^^^^^
KeyError: '10P30N'
