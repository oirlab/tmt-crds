"""This module is the interface to CRDS configuration information.  Predominantly
it is used to define CRDS file cache paths and file location functions.
"""

import os
import os.path

# ===========================================================================

DEFAULT_CRDS_DIR = "./crds"

def get_crds_path():
    """Return the root directory of the CRDS cache."""
    return os.environ.get("CRDS_PATH", DEFAULT_CRDS_DIR)

# ===========================================================================

def get_crds_mappath():
    """get_crds_mappath() returns the base path of the CRDS mapping directory 
    tree where CRDS rules files (mappings) are stored.   This is extended by
    <observatory> once it is known.
    """
    try:
        return os.environ["CRDS_MAPPATH"]
    except KeyError:
        return  get_crds_path() + "/mappings"

def get_crds_refpath():
    """get_crds_refpath returns the base path of the directory tree where CRDS 
    reference files are stored.   This is extended by <observatory> once it is
    known.
    """
    try:
        return os.environ["CRDS_REFPATH"]
    except KeyError:
        return get_crds_path() + "/references"

def get_crds_config_path():
    """Return the path to a writable directory used to store configuration info
    such as last known server status.   This is extended by <observatory> once
    it is known.   If CRDS_PATH doesn't point to a writable directory, then
    CRDS_CFGPATH should be defined.
    """
    try:
        return os.environ["CRDS_CFGPATH"]
    except KeyError:
        return get_crds_path() + "/config"

def get_crds_processing_mode():
    """Return the preferred location for computing best references when
    network connectivity is available.
    
    'local'   --   compute locally even if client CRDS is obsolete
    'remote'  --   compute remotely even if client CRDS is up-to-date
    'auto'    --   compute locally unless connected and client CRDS is obsolete
    """
    mode = os.environ.get("CRDS_MODE","auto")
    assert mode in ["local", "remote", "auto"], "Invalid CRDS processing mode: " + repr(mode)
    return mode

# ===========================================================================

def locate_file(filepath, observatory):
    """Figure out the absolute pathname where CRDS will stash a reference
    or mapping file.  If filepath already has a directory,  return filepath
    as-is.   Otherwise,  return the *client* path for a file.
    """
    if os.path.dirname(filepath):
        return filepath
    if is_mapping(filepath):
        return locate_mapping(filepath, observatory)
    else:
        return locate_reference(filepath, observatory)

def locate_reference(ref, observatory):
    """Return the absolute path where reference `ref` should be located."""
    if os.path.dirname(ref):
        return ref
    return os.path.join(get_crds_refpath(), observatory, ref)

def is_mapping(mapping):
    """Return True IFF `mapping` has an extension indicating a CRDS mapping 
    file.
    """
    return mapping.endswith((".pmap", ".imap", ".rmap"))

def locate_mapping(mappath, observatory=None):
    """Return the path where CRDS mapping `mappath` should be."""
    if os.path.dirname(mappath):
        return mappath
    if observatory is None:
        observatory = mapping_to_observatory(mappath)
    return os.path.join(get_crds_mappath(), observatory, mappath)

def mapping_exists(mapping):
    """Return True IFF `mapping` exists on the local file system."""
    return os.path.exists(locate_mapping(mapping))


# These are name based but could be written as slower check-the-mapping
# style functions.
def mapping_to_observatory(context_file):
    """
    >>> mapping_to_observatory('hst_acs_biasfile.rmap')
    'hst'
    """
    return os.path.basename(context_file).split("_")[0].split(".")[0]

def mapping_to_instrument(context_file):
    """
    >>> mapping_to_instrument('hst_acs_biasfile.rmap')
    'acs'
    """
    return os.path.basename(context_file).split("_")[1].split(".")[0]

def mapping_to_filekind(context_file):
    """
    >>> mapping_to_filekind('hst_acs_biasfile.rmap')
    'biasfile'
    """
    return os.path.basename(context_file).split("_")[2].split(".")[0]

