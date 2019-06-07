"""This module provides functions that interface with the JWST calibration code to determine
things like "reference types used by a pipeline."

>>> header_to_reftypes(test_header("0.7.0", "FGS_DARK"))
['ipc', 'linearity', 'mask', 'refpix', 'rscd', 'saturation', 'superbias']

>>> header_to_reftypes(test_header("0.7.0", "NRS_BRIGHTOBJ"))
['area', 'camera', 'collimator', 'dark', 'disperser', 'distortion', 'drizpars', 'extract1d', 'filteroffset', 'fore', 'fpa', 'fringe', 'gain', 'ifufore', 'ifupost', 'ifuslicer', 'ipc', 'linearity', 'mask', 'msa', 'ote', 'pathloss', 'photom', 'readnoise', 'refpix', 'regions', 'rscd', 'saturation', 'specwcs', 'straymask', 'superbias', 'v2v3', 'wavelengthrange']

>>> header_to_reftypes(test_header("0.7.0", "MIR_IMAGE"))
['area', 'camera', 'collimator', 'dark', 'disperser', 'distortion', 'filteroffset', 'flat', 'fore', 'fpa', 'gain', 'ifufore', 'ifupost', 'ifuslicer', 'ipc', 'linearity', 'mask', 'msa', 'ote', 'photom', 'readnoise', 'refpix', 'regions', 'rscd', 'saturation', 'specwcs', 'superbias', 'v2v3', 'wavelengthrange']

>>> header_to_reftypes(test_header("0.7.0", "MIR_LRS-FIXEDSLIT"))
['area', 'camera', 'collimator', 'dark', 'disperser', 'distortion', 'drizpars', 'extract1d', 'filteroffset', 'flat', 'fore', 'fpa', 'fringe', 'gain', 'ifufore', 'ifupost', 'ifuslicer', 'ipc', 'linearity', 'mask', 'msa', 'ote', 'pathloss', 'photom', 'readnoise', 'refpix', 'regions', 'rscd', 'saturation', 'specwcs', 'straymask', 'superbias', 'v2v3', 'wavelengthrange']

>>> header_to_pipelines(test_header("0.7.0", "FGS_DARK"))
['calwebb_dark.cfg', 'skip_2b.cfg']

>>> header_to_pipelines(test_header("0.7.0", "NRS_BRIGHTOBJ"))
['calwebb_sloper.cfg', 'calwebb_spec2.cfg']

>>> header = test_header("0.13.0", "MIR_IMAGE", tsovisit="F")
>>> header_to_pipelines(header)
['calwebb_detector1.cfg', 'calwebb_image2.cfg']
    
>>> header = test_header("0.13.0", "MIR_IMAGE", tsovisit="T")
>>> header_to_pipelines(header)
['calwebb_detector1.cfg', 'calwebb_tso-image2.cfg']

>>> header_to_pipelines(test_header("0.7.0", "MIR_IMAGE"))
['calwebb_sloper.cfg', 'calwebb_image2.cfg']
    
>>> header_to_pipelines(test_header("0.7.0", "MIR_LRS-FIXEDSLIT"))
['calwebb_sloper.cfg', 'calwebb_spec2.cfg']

>>> _get_missing_calver("0.7.0")
'0.7.0'

>>> s = _get_missing_calver(None)
>>> isinstance(s, str)
True

>>> s = _get_missing_calver()
>>> isinstance(s, str)
True

>>> _get_missing_context()
'jwst-operational'

>>> _get_missing_context('jwst_0341.pmap')
'jwst_0341.pmap'

>>> os.path.basename(_get_config_refpath("jwst_0552.pmap", "0.7.7"))
'jwst_system_crdscfg_b7.yaml'

>>> os.path.basename(_get_config_refpath("jwst_0552.pmap", "0.9.3"))
'jwst_system_crdscfg_b7.1.3.yaml'

>>> os.path.basename(_get_config_refpath("jwst_0552.pmap", "0.9.7"))
'jwst_system_crdscfg_b7.1.3.yaml'

>>> os.path.basename(_get_config_refpath("jwst_0477.pmap", "0.10.1"))
'jwst_system_crdscfg_b7.2.yaml'
"""

import os.path
from collections import defaultdict
import re

# import yaml     DEFERRED

from pkg_resources import parse_version

# --------------------------------------------------------------------------------------

# from jwst import version     DEFERRED

# --------------------------------------------------------------------------------------
import crds
from crds.core import log, utils
from crds.core.log import srepr
from crds.client import api

# --------------------------------------------------------------------------------------

def test_header(calver, exp_type, tsovisit="F", lamp_state="NONE"):
    """Create a header-like dictionary from `calver` and `exp_type` to
    support testing header-based functions.
    """
    header = {
        "META.INSTRUMENT.NAME" : "SYSTEM",
        "REFTYPE" : "CRDSCFG",
        "META.CALIBRATION_SOFTWARE_VERSION" : calver,
        "META.EXPOSURE.TYPE" : exp_type,
        "META.VISIT.TSOVISIT" : tsovisit,
        "META.INSTRUMENT.LAMP_STATE" : lamp_state,
        }
    return header

# --------------------------------------------------------------------------------------

def _get_missing_calver(cal_ver=None):
    """If `cal_ver` is None, return the calibration software version for 
    the installed version of calibration code.  Otherwise return `cal_ver`
    unchanged.
    """
    if cal_ver is None:
        from jwst import version
        cal_ver = version.__version__
    return cal_ver

def _get_missing_context(context=None):
    """Default the context to `jwst-operational` if `context` is None, otherwise
    return context unchanged.
    """
    return "jwst-operational" if context is None else context
    
# --------------------------------------------------------------------------------------

def header_to_reftypes(header, context=None):
    """Given a dataset `header`,  extract the EXP_TYPE or META.EXPOSURE.TYPE keyword
    from and use it to look up the reftypes required to process it.

    Return a list of reftype names.
    """
    with log.augment_exception("Failed determining exp_type, cal_ver from header", log.PP(header)):
        exp_type, cal_ver = _header_to_exptype_calver(header)
    config_manager = _get_config_manager(context, cal_ver)
    pipelines = header_to_pipelines(header, context)
    reftypes = set()
    for cfg in pipelines:
        steps = config_manager.pipeline_cfgs_to_steps[cfg]
        for step in steps:
            reftypes |= set(config_manager.steps_to_reftypes[step])
    return sorted(list(reftypes))

def get_reftypes(exp_type, cal_ver=None, context=None):
    """Given `exp_type` and `cal_ver` and `context`,  locate the appropriate SYSTEM CRDSCFG
    reference file and determine the reference types required to process every pipeline Step
    nominally associated with that exp_type.
    """
    with log.warn_on_exception("Failed determining required reftypes from",
                               "EXP_TYPE", srepr(exp_type)):
        config_manager = _get_config_manager(context, cal_ver)
        return config_manager.exptype_to_reftypes(exp_type)
    return []

# This is potentially an external interface to system data processing (SDP) / the archive pipeline.
def header_to_pipelines(header, context=None):
    """Given a dataset `header`,  extract the EXP_TYPE or META.EXPOSURE.TYPE keyword
    from and use it to look up the pipelines required to process it.

    Return a list of pipeline .cfg names.
    """
    with log.augment_exception("Failed determining exp_type, cal_ver from header", log.PP(header)):
        exp_type, cal_ver = _header_to_exptype_calver(header)
    config_manager = _get_config_manager(context, cal_ver)
    pipelines = get_pipelines(exp_type, cal_ver, context)
    if config_manager.pipeline_exceptions:
        pipelines2 = []
        for cfg in pipelines:
            for param, exceptions in config_manager.pipeline_exceptions.items():
                paramval = header.get(param.upper(), "F")
                if paramval not in ["F", "FALSE", "NONE", "OFF"]:
                    # tsovisit, lamp_state
                    cfg = exceptions.get(cfg, cfg)
            pipelines2.append(cfg)
        pipelines = pipelines2
    log.verbose("Applicable pipelines for", srepr(exp_type), "are", srepr(pipelines))
    return pipelines

def get_pipelines(exp_type, cal_ver=None, context=None):
    """Given `exp_type` and `cal_ver` and `context`,  locate the appropriate SYSTEM CRDSCFG
    reference file and determine the sequence of pipeline .cfgs required to process that
    exp_type.
    """
    with log.augment_exception("Failed determining required pipeline .cfgs for",
                               "EXP_TYPE", srepr(exp_type)):
        config_manager = _get_config_manager(context, cal_ver)
        return config_manager.exptype_to_pipelines(exp_type)

def reftype_to_pipelines(reftype, cal_ver=None, context=None):
    """Given `exp_type` and `cal_ver` and `context`,  locate the appropriate SYSTEM CRDSCFG
    reference file and determine the sequence of pipeline .cfgs required to process that
    exp_type.
    """
    with log.augment_exception("Failed determining required pipeline .cfgs for",
                               "REFTYPE", srepr(reftype)):
        config_manager = _get_config_manager(context, cal_ver)
        return config_manager.reftype_to_pipelines(reftype)

def _header_to_exptype_calver(header):
    """Given dataset `header`,  return the EXP_TYPE and CAL_VER values."""
    cal_ver = header.get("META.CALIBRATION_SOFTWARE_VERSION", header.get("CAL_VER"))
    cal_ver = _get_missing_calver(cal_ver)
    exp_type = header.get("META.EXPOSURE.TYPE",  header.get("EXP_TYPE", "UNDEFINED"))
    return exp_type, cal_ver

@utils.cached  # for caching,  pars must be immutable, ideally simple
def _get_config_manager(context, cal_ver):
    """Given `context` and calibration s/w version `cal_ver`,  identify the appropriate
    SYSTEM CRDSCFG reference file and create a CrdsCfgManager from it.
    """
    refpath = _get_config_refpath(context, cal_ver)
    return _load_refpath(context, refpath)

def _load_refpath(context, refpath):
    """Given `context` and SYSTEM CRDSCFG reference at `refpath`,  construct a CrdsCfgManager."""
    import yaml
    with open(refpath) as opened:
        crdscfg =  yaml.safe_load(opened)
    return CrdsCfgManager(context, refpath, crdscfg)

# --------------------------------------------------------------------------------------

HERE = os.path.dirname(__file__) or "."

REFPATHS = [
    ('0.7.7', "jwst_system_crdscfg_b7.yaml"),
    ('0.9.0', "jwst_system_crdscfg_b7.1.yaml"),
    ('0.9.1', "jwst_system_crdscfg_b7.1.1.yaml"),
    ('0.9.3', "jwst_system_crdscfg_b7.1.3.yaml"),
    ('0.10.0', "jwst_system_crdscfg_b7.2.yaml"),
    ('0.13.0', "jwst_system_crdscfg_b7.3.yaml"),
    ('999.0.0', "jwst_system_crdscfg_b7.3.yaml"),   # latest backstop
]
    
def _get_config_refpath(context, cal_ver):
    """Given CRDS `context` and calibration s/w version `cal_ver`,  identify the applicable
    SYSTEM CRDSCFG reference file, cache it, and return the file path.
    """
    context = _get_missing_context(context)
    cal_ver = _get_missing_calver(cal_ver)
    i = 0
    while (i < len(REFPATHS)-1 and not _versions_lt(cal_ver, REFPATHS[i+1][0])):
        i += 1
    refpath = os.path.join(HERE, REFPATHS[i][1])
    try:  # Use a normal try/except because exceptions are expected.
        header = {
            "META.INSTRUMENT.NAME" : "SYSTEM", 
            "META.CALIBRATION_SOFTWARE_VERSION": cal_ver 
        }
        pmap = crds.get_symbolic_mapping(context)
        imap = pmap.get_imap("system")
        rmapping = imap.get_rmap("crdscfg")
        ref = rmapping.get_best_ref(header)
        refpath = rmapping.locate_file(ref)
        api.dump_references(context, [ref])
    except Exception:
        log.verbose_warning(
            "Failed locating SYSTEM CRDSCFG reference",
            "under context", repr(context),
            "and cal_ver", repr(cal_ver) + ".   Using built-in references.")
    log.verbose("Using", srepr(os.path.basename(refpath)),
                "to determine applicable default reftypes for", srepr(cal_ver))
    return refpath

def _versions_lt(v1, v2):
    """Compare two semantic version numbers and account for issues like '10' < '9'.
    Return True IFF `v1` < `v2`.

    >>> _versions_gte("0.7.7", "0.7.7")
    True
    >>> _versions_gte("0.7.8", "0.7.7")
    True
    >>> _versions_gte("0.7.6", "0.7.7")
    False
    >>> _versions_gte("0.7.7", "0.7.8")
    False
    >>> _versions_gte("0.7.7", "0.7.6")
    True
    >>> _versions_gte("0.10.1", "0.7.7")
    True
    >>> _versions_gte("0.10.1", "0.10.0")
    True
    >>> _versions_gte("0.10.0", "0.10.1")
    False
    >>> _versions_gte("0.10.1", "0.10.1")
    True
    >>> _versions_gte("0.10.1", "0.10.1a1")
    True
    >>> _versions_gte("0.10.2", "0.10.1a1")
    True
    >>> _versions_gte("0.10.1", "0.11.1a1")
    False
    >>> _versions_gte("0.9.7", "0.10.0")
    False
    >>> _versions_gte("0.9.2", "0.10.1dev20000")
    False
    >>> _versions_gte("0.99.7", "0.10.1dev20000")
    True
    >>> _versions_gte("0.10.1", "0.10.1dev20000")
    True
    """
    return parse_version(v1) < parse_version(v2)

def _versions_gte(v1, v2):
    """"""
    return parse_version(v1) >= parse_version(v2)

class CrdsCfgManager:
    """The CrdsCfgManager handles using SYSTEM CRDSCFG information to compute things."""
    def __init__(self, context, refpath, crdscfg):
        self._context = context
        self._refpath = refpath
        self._crdscfg = utils.Struct(crdscfg)
        self.pipeline_exceptions = self._crdscfg.get("pipeline_exceptions", {})
        self.pipeline_cfgs_to_steps = self._crdscfg.get("pipeline_cfgs_to_steps", {})
        self.steps_to_reftypes = self._crdscfg.get("steps_to_reftypes", {})
        
    def exptype_to_reftypes(self, exp_type):
        """For a given EXP_TYPE string, return a list of reftypes needed to process that
        EXP_TYPE through the data levels appropriate for that EXP_TYPE.

        Return [reftypes, ... ]
        """
        reftypes = self._crdscfg.exptypes_to_reftypes[exp_type]
        log.verbose("Applicable reftypes for", srepr(exp_type), 
                    "determined by", srepr(os.path.basename(self._refpath)),
                    "are", srepr(reftypes))
        return reftypes

    def exptype_to_pipelines(self, exp_type):
        """For a given EXP_TYPE string, return a list of pipeline .cfg's needed to 
        process that EXP_TYPE through the appropriate data levels.

        Return [.cfg's, ... ]
        """
        pipelines = self._crdscfg.exptypes_to_pipelines[exp_type]
        return pipelines

    def reftype_to_pipelines(self, reftype):
        pipelines = []
        reftypes_to_steps = invert_list_mapping(self._crdscfg.steps_to_reftypes)
        steps_to_pipelines = invert_list_mapping(self._crdscfg.pipeline_cfgs_to_steps)
        for step in reftypes_to_steps[reftype]:
            pipelines += steps_to_pipelines[step]
        return list(sorted(set(pipelines)))

def invert_list_mapping(mapping):
    """Invert a dictionary of lists into another dictionary of lists such that each
    element of each original list is a key somewhere in the inversion, and each key is
    an element of at least one list in the inversion.
    """
    inverted = defaultdict(set)
    for key, values in mapping.items():
        for value in values:
            inverted[value].add(key)
    return { key:list(sorted(values)) 
             for (key,values) in inverted.items() }

def scan_exp_type_coverage():
    """Verify that there is some get_reftypes() response for all available exp_types."""
    from . import schema as crds_schema
    exp_types = crds_schema.get_exptypes()
    for exp_type in exp_types:
        if exp_type in ["ANY","N/A"]:
            continue
        with log.warn_on_exception("failed determining reftypes for", repr(exp_type)):
            reftypes = get_reftypes(exp_type)
            log.verbose("Reftypes for", repr(exp_type), "=", repr(reftypes))

def test():
    """Run the module doctests."""
    import doctest
    from crds.jwst import pipeline
    return doctest.testmod(pipeline)

# --------------------------------------------------------------------------------------

if __name__ == "__main__":
    print(test())
