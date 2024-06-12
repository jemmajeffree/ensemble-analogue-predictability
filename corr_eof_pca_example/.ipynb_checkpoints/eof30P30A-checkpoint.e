Traceback (most recent call last):
  File "/glade/u/home/jjeffree/ensemble-analogue-predictability/eof_calculation.py", line 23, in <module>
    import predictability_tools as pt
  File "/glade/u/home/jjeffree/ensemble-analogue-predictability/predictability_tools/__init__.py", line 8, in <module>
    from .mask_definitions import mask_dict
  File "/glade/u/home/jjeffree/ensemble-analogue-predictability/predictability_tools/mask_definitions.py", line 16, in <module>
    mask_dict['5P'] = pacific_mask.where(np.abs(pacific_mask['lat'])<5,0)
                                         ^^
NameError: name 'np' is not defined
