Traceback (most recent call last):
  File "/glade/u/home/jjeffree/ensemble-analogue-predictability/analogue_forecasting2.py", line 123, in <module>
    os.mkdir('/'.join(out_filename.split('/')[:-1])) # Should also throw an error if there's any other problems with this directory existing
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileExistsError: [Errno 17] File exists: '/glade/work/jjeffree/results/area_corr/multiindex/GFDL-CM2-1_tos_zos'
