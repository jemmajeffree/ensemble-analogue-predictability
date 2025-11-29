/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/distributed/node.py:182: UserWarning: Port 8787 is already in use.
Perhaps you already have a cluster running?
Hosting the HTTP server on port 34431 instead
  warnings.warn(
Traceback (most recent call last):
  File "/glade/u/home/jjeffree/ensemble-analogue-predictability/analogue_forecasting2.py", line 123, in <module>
    os.mkdir('/'.join(out_filename.split('/')[:-1])) # Should also throw an error if there's any other problems with this directory existing
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/glade/work/jjeffree/results/area_corr/multiindex/ACCESS-ESM1-5_nomean_tos_zos'
