### BRANCHED from eofs package https://github.com/ajdawson/eofs.git at commit 9d206001a1d841fa649dce359554d43e315801b6
(Fri Sep 30 2022)
The following updates have been made (basically just tweaking to match new numpy, and commenting out the bit that was causing problems with multi-indexes. Ideally I'll go through and raise an issue (hopefully also a PR) in future to address this

@@ -121,7 +121,7 @@ class Eof(object):
         # Store information about the shape/size of the input data.
         self._records = self._data.shape[0]
         self._originalshape = self._data.shape[1:]
-        channels = np.product(self._originalshape)
+        channels = np.prod(self._originalshape)
         # Weight the data set according to weighting argument.
         if weights is not None:
             try:
@@ -193,7 +193,7 @@ class Eof(object):
         # astype method to ensure the eigenvectors are the same type as the
         # input dataset since multiplication by np.NaN will promote to 64-bit.
         self._flatE = np.ones([self.neofs, channels],
-                              dtype=self._data.dtype) * np.NaN
+                              dtype=self._data.dtype) * np.nan
         self._flatE = self._flatE.astype(self._data.dtype)
         self._flatE[:, nonMissingIndex] = E
         # Remove the scaling on the principal component time-series that is
@@ -735,7 +735,7 @@ class Eof(object):
         if eof_ndim > input_ndim:
             field = field.reshape((1,) + field.shape)
         records = field.shape[0]
-        channels = np.product(field.shape[1:])
+        channels = np.prod(field.shape[1:])
         field_flat = field.reshape([records, channels])
         # Locate the non-missing values and isolate them.
         if not self._valid_nan(field_flat):
diff --git a/lib/eofs/tools/standard.py b/lib/eofs/tools/standard.py
index b4ed837..9863c89 100644
--- a/lib/eofs/tools/standard.py
+++ b/lib/eofs/tools/standard.py
@@ -46,7 +46,7 @@ def _check_flat_center(pcs, field):
     else:
         # Record the shape of the field and the number of spatial elements.
         originalshape = field.shape[1:]
-        channels = np.product(originalshape)
+        channels = np.prod(originalshape)
     # Record the number of PCs.
     if len(pcs.shape) == 1:
         npcs = 1
diff --git a/lib/eofs/xarray.py b/lib/eofs/xarray.py
index 70b1c86..5d641fd 100644
--- a/lib/eofs/xarray.py
+++ b/lib/eofs/xarray.py
@@ -178,8 +178,8 @@ class Eof(object):
                                  attrs={'long_name': 'eof_mode_number'})
         coords = [self._time, pcdim]
         pcs = xr.DataArray(pcs, coords=coords, name='pcs')
-        pcs.coords.update({coord.name: ('time', coord.data)
-                           for coord in self._time_ndcoords})
+        #pcs.coords.update({coord.name: ('time', coord.data)
+        #                   for coord in self._time_ndcoords})
         return pcs
 
     def eofs(self, eofscaling=0, neofs=None):
@@ -226,8 +226,8 @@ class Eof(object):
         long_name = 'empirical_orthogonal_functions'
         eofs = xr.DataArray(eofs, coords=coords, name='eofs',
                             attrs={'long_name': long_name})
-        eofs.coords.update({coord.name: (coord.dims, coord.data)
-                            for coord in self._space_ndcoords})
+        #eofs.coords.update({coord.name: (coord.dims, coord.data)
+        #                    for coord in self._space_ndcoords})
         return eofs
 
     def eofsAsCorrelation(self, neofs=None):
@@ -333,8 +333,8 @@ class Eof(object):
         long_name = 'covariance_between_pcs_and_{!s}'.format(self._name)
         eofs = xr.DataArray(eofs, coords=coords, name='eofs',
                             attrs={'long_name': long_name})
-        eofs.coords.update({coord.name: (coord.dims, coord.data)
-                            for coord in self._space_ndcoords})
+        #eofs.coords.update({coord.name: (coord.dims, coord.data)
+        #                    for coord in self._space_ndcoords})
         return eofs
 
     def eigenvalues(self, neigs=None):



eofs - EOF analysis in Python
=============================

[![Build Status](https://travis-ci.org/ajdawson/eofs.svg?branch=master)](https://travis-ci.org/ajdawson/eofs) [![DOI (paper)](https://img.shields.io/badge/DOI%20%28paper%29-10.5334%2Fjors.122-blue.svg)](http://doi.org/10.5334/jors.122) [![DOI (latest release)](https://zenodo.org/badge/20448/ajdawson/eofs.svg)](https://zenodo.org/badge/latestdoi/20448/ajdawson/eofs)


Overview
--------

eofs is a Python package for performing empirical orthogonal function (EOF) analysis on spatial-temporal data sets, licensed under the GNU GPLv3.

The package was created to simplify the process of EOF analysis in the Python environment.
Some of the key features are listed below:

* Suitable for large data sets: computationally efficient for the large data sets typical of modern climate model output.
* Transparent handling of missing values: missing values are removed automatically when computing EOFs and re-inserted into output fields.
* Meta-data preserving interfaces (optional): works with the iris data analysis package, xarray, or the cdms2 module (from UV-CDAT) to carry meta-data over from input fields to output.
* No Fortran dependencies: written in Python using the power of NumPy, no compilers required.


Requirements
------------

eofs only requires the NumPy package (and setuptools to install).
In order to use the meta-data preserving interfaces one (or more) of cdms2 (part of [UV-CDAT](http://uvcdat.llnl.gov/)), [iris](http://scitools.org.uk/iris), or [xarray](http://xarray.pydata.org) is needed.


Documentation
-------------

Documentation is available [online](http://ajdawson.github.io/eofs).
The package docstrings are also very complete and can be used as a source of reference when working interactively.


Citation
--------

If you use eofs in published research, please cite it by referencing the [peer-reviewed paper](http://doi.org/10.5334/jors.122).
You can additionally cite the [Zenodo DOI](http://dx.doi.org/10.5281/zenodo.46871) if you need to cite a particular version (but please also cite the paper, it helps me justify my time working on this and similar projects).


Installation
------------

eofs works on Python 2 or 3 on Linux, Windows or OSX.
The easiest way to install eofs is by using [conda](http://conda.pydata.org/docs/) or pip:

    conda install -c conda-forge eofs

or

    pip install eofs

You can also install from the source distribution:

    python setup.py install


Frequently asked questions
--------------------------

* **Do I need UV-CDAT/cdms2, iris or xarray to use eofs?**
  No. All the computation code uses NumPy only.
  The cdms2 module, iris and xarray are only required for the meta-data preserving interfaces.
