Traceback (most recent call last):
  File "/glade/u/home/jjeffree/ensemble-analogue-predictability/analogue_forecasting2.py", line 123, in <module>
    os.mkdir('/'.join(out_filename.split('/')[:-1])) # Should also throw an error if there's any other problems with this directory existing
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/glade/work/jjeffree/results/area_corr//multiindex/ACCESS-ESM1-5_nomean_tos_zos'
