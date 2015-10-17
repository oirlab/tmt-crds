from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os

import crds
from crds import utils, log, client, config
from crds.bestrefs import BestrefsScript
from crds.tests import test_config
from crds import tests

# Contrived headers which will select bad files.

HST_HEADER = {
    'INSTRUME' : 'ACS',
    'REFTYPE' : 'PFLTFILE',
    'DETECTOR': 'SBC',
    'CCDAMP': 'N/A',
    'FILTER1' : 'PR110L',
    'FILTER2' : 'N/A',
    'OBSTYPE': 'SPECTROSCOPIC',
    'FW1OFFST' : 'N/A',
    'FW2OFFST': 'N/A',
    'FWOFFST': 'N/A',
    'DATE-OBS': '1991-01-01',
    'TIME-OBS': '00:00:00'
    }

JWST_HEADER = {
    "meta.instrument.name": "NIRISS",
    "meta.observation.date": "2012-07-25T00:00:00",
    "meta.instrument.detector" : "NIRISS",
    "meta.instrument.filter" : "CLEAR",
    "meta.subarray.name" : "FULL",
    }

def dt_bad_references_error_cache_config():
    """
    CRDS can designate files as scientifically invalid which is reflected in the catalog
    on a the CRDS server and also recorded in the configuration info and as a bad files list
    which are written down in the "config" directory.
    
    A key aspect of bad files management is the location and contents of the cache config
    directory.  The current HST cache in trunk/crds/cache has a config area and 4 bad files.
    
    The default handling when a bad reference file is assigned is to raise an exception:
    
    >>> old_state = test_config.setup(clear_existing=False)
    >>> config.ALLOW_BAD_RULES.reset()
    >>> config.ALLOW_BAD_REFERENCES.reset()

    >>> crds.getreferences(HST_HEADER, observatory='hst', context='hst_0282.pmap', reftypes=['pfltfile'])
    Traceback (most recent call last):
    ...
    CrdsBadReferenceError: Recommended reference 'l2d0959cj_pfl.fits' of type 'pfltfile' is designated scientifically invalid.
    <BLANKLINE>

    >>> test_config.cleanup(old_state)
    """
    
def dt_bad_references_warning_cache_config():
    """
    A secondary behaviour is to permit use of bad references with a warning:
    
    >>> old_state = test_config.setup(clear_existing=False)
    >>> config.ALLOW_BAD_RULES.set("1")
    >>> config.ALLOW_BAD_REFERENCES.set("1")
    
    >>> crds.getreferences(HST_HEADER, observatory='hst', context='hst_0282.pmap', reftypes=['pfltfile'])    # doctest: +ELLIPSIS
    CRDS  : WARNING  Recommended reference 'l2d0959cj_pfl.fits' of type 'pfltfile' is designated scientifically invalid.
    <BLANKLINE>
    {'pfltfile': '.../l2d0959cj_pfl.fits'}

    >>> test_config.cleanup(old_state)
    """
    
def dt_bad_references_fast_mode():
    """
    When run in 'fast' mode as is done for the calls from crds.bestrefs,  no exception or warning is possible:
    
    >>> old_state = test_config.setup(clear_existing=False)
    >>> config.ALLOW_BAD_RULES.reset()
    >>> config.ALLOW_BAD_REFERENCES.reset()
    
    >>> crds.getreferences(HST_HEADER, observatory='hst', context='hst_0282.pmap', reftypes=['pfltfile'], fast=True) # doctest: +ELLIPSIS
    {'pfltfile': '/grp/crds/cache/references/hst/l2d0959cj_pfl.fits'}

    >>> test_config.cleanup(old_state)
    """


def dt_bad_references_bestrefs_script_error():
    """
    The crds.bestrefs program handles bad files differently because it frequently operates on
    multiple contexts at the same time,  and recommending bad files under the old context is OK.
    
    >>> old_state = test_config.setup(clear_existing=False)
    >>> config.ALLOW_BAD_RULES.reset()
    >>> config.ALLOW_BAD_REFERENCES.reset()
    
    By default,  in crds.bestrefs use of a bad reference is an error:

    >>> BestrefsScript("crds.bestrefs --new-context hst_0282.pmap --files data/j8btxxx_raw_bad.fits")()
    CRDS  : INFO     No comparison context or source comparison requested.
    CRDS  : INFO     No file header updates requested;  dry run.
    CRDS  : INFO     ===> Processing data/j8btxxx_raw_bad.fits
    CRDS  : ERROR    instrument='ACS' type='PFLTFILE' data='data/j8btxxx_raw_bad.fits' ::  File 'L2D0959CJ_PFL.FITS' is bad. Use is not recommended,  results may not be scientifically valid.
    CRDS  : INFO     1 errors
    CRDS  : INFO     0 warnings
    CRDS  : INFO     3 infos
    1
    
    >>> test_config.cleanup(old_state)
    """
    
def dt_bad_references_bestrefs_script_warning():
    """
    >>> old_state = test_config.setup(clear_existing=False)
    >>> config.ALLOW_BAD_RULES.set("1")
    >>> config.ALLOW_BAD_REFERENCES.set("1")
    
    >>> BestrefsScript("crds.bestrefs --new-context hst_0282.pmap --files data/j8btxxx_raw_bad.fits --allow-bad-references")() # doctest: +ELLIPSIS
    CRDS  : INFO     No comparison context or source comparison requested.
    CRDS  : INFO     No file header updates requested;  dry run.
    CRDS  : INFO     ===> Processing data/j8btxxx_raw_bad.fits
    CRDS  : WARNING  For data/j8btxxx_raw_bad.fits ACS pfltfile File 'L2D0959CJ_PFL.FITS' is bad. Use is not recommended,  results may not be scientifically valid.
    CRDS  : INFO     0 errors
    CRDS  : INFO     1 warnings
    CRDS  : INFO     3 infos
    0
    
    >>> test_config.cleanup(old_state)
    """

def dt_bad_references_bestrefs_script_deprecated():
    """
    As a backward compatibility measure,  the --bad-files-are-errors switch is still accepted but is a tautology:
    
    >>> old_state = test_config.setup(clear_existing=False)
    >>> config.ALLOW_BAD_RULES.reset()
    >>> config.ALLOW_BAD_REFERENCES.reset()
    
    >>> BestrefsScript("crds.bestrefs --new-context hst_0282.pmap --files data/j8btxxx_raw_bad.fits --bad-files-are-errors")() # doctest: +ELLIPSIS
    CRDS  : INFO     No comparison context or source comparison requested.
    CRDS  : INFO     No file header updates requested;  dry run.
    CRDS  : INFO     ===> Processing data/j8btxxx_raw_bad.fits
    CRDS  : ERROR    instrument='ACS' type='PFLTFILE' data='data/j8btxxx_raw_bad.fits' ::  File 'L2D0959CJ_PFL.FITS' is bad. Use is not recommended,  results may not be scientifically valid.
    CRDS  : INFO     1 errors
    CRDS  : INFO     0 warnings
    CRDS  : INFO     3 infos
    1

    >>> test_config.cleanup(old_state)
    """

def dt_bad_rules_jwst_getreferences_error():
    """
    There is also a check for use of bad rules. JWST has a few,  including jwst_0017.pmap by "inheritance"
    since it includes some bad rules.
    
    Do some setup to switch to a JWST serverless mode.
    
    >>> old_state = test_config.setup(cache=tests.CRDS_SHARED_GROUP_CACHE, url="https://jwst-serverless-mode.stsci.edu")    
    >>> config.ALLOW_BAD_RULES.reset()
    >>> config.ALLOW_BAD_REFERENCES.reset()
    
    >>> crds.getreferences(JWST_HEADER, observatory='jwst', context='jwst_0017.pmap', reftypes=["flat"])
    Traceback (most recent call last):
    ...
    CrdsBadRulesError: Final context 'jwst_0017.pmap' is marked as scientifically invalid based on: ['jwst_miri_flat_0003.rmap']
    <BLANKLINE>

    >>> test_config.cleanup(old_state)
    """

def dt_bad_rules_jwst_getreferences_warning():
    """
    Similarly,  the use of bad rules can be permitted:
    
    >>> old_state = test_config.setup(cache=tests.CRDS_SHARED_GROUP_CACHE, url="https://jwst-serverless-mode.stsci.edu")    
    >>> config.ALLOW_BAD_RULES.set("1")
    
    >>> refs = crds.getreferences(JWST_HEADER, observatory='jwst', context='jwst_0017.pmap', reftypes=["flat"])   # doctest: +ELLIPSIS
    CRDS  : INFO     Using CACHED CRDS reference assignment rules last updated on '...'
    CRDS  : WARNING  Final context 'jwst_0017.pmap' is marked as scientifically invalid based on: ['jwst_miri_flat_0003.rmap']
    <BLANKLINE>
    
    >>> list(refs.keys()) == ['flat']
    True
    
    >>> os.path.basename(refs['flat']) == 'jwst_niriss_flat_0000.fits'
    True

    >>> test_config.cleanup(old_state)
    """

def dt_bad_rules_jwst_bestrefs_script_error():
    """
    Here try bad rules for a JWST dataset:
    
    >>> old_state = test_config.setup(cache=tests.CRDS_SHARED_GROUP_CACHE, url="https://jwst-serverless-mode.stsci.edu")    
    >>> config.ALLOW_BAD_RULES.reset()
    
    >>> BestrefsScript("crds.bestrefs --jwst --new-context jwst_0017.pmap --files data/jw_nrcb1_uncal_sloper_image.fits --types gain")()   # doctest: +ELLIPSIS
    CRDS  : INFO     Using CACHED CRDS reference assignment rules last updated on '...'
    CRDS  : ERROR    instrument='ALL' type='ALL' data='ALL' ::  New-context = 'jwst_0017.pmap' is bad or contains bad rules.  Use is not recommended,  results may not be scientifically valid.
    CRDS  : INFO     No comparison context or source comparison requested.
    CRDS  : INFO     No file header updates requested;  dry run.
    CRDS  : INFO     ===> Processing data/jw_nrcb1_uncal_sloper_image.fits
    CRDS  : ERROR    Failed processing 'data/jw_nrcb1_uncal_sloper_image.fits' : Failed computing bestrefs for data 'data/jw_nrcb1_uncal_sloper_image.fits' with respect to 'jwst_0017.pmap' : Final context 'jwst_0017.pmap' is marked as scientifically invalid based on: ['jwst_miri_flat_0003.rmap']
    <BLANKLINE>
    CRDS  : INFO     2 errors
    CRDS  : INFO     0 warnings
    CRDS  : INFO     4 infos
    2
    
    >>> test_config.cleanup(old_state)
    """

def main():
    """Run module tests,  for now just doctests only."""
    from crds.tests import test_bad_files, tstmod
    return tstmod(test_bad_files)

if __name__ == "__main__":
    print(main())
