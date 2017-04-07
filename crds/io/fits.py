'''
Created on Feb 15, 2017

@author: jmiller
'''
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

# ============================================================================

import contextlib

from astropy.io import fits

# ============================================================================

from crds.core import python23, config, utils, log

from .abstract import AbstractFile, ArrayFormat, hijack_warnings

# ============================================================================

@contextlib.contextmanager
@utils.gc_collected
def fits_open(filename, **keys):
    """Return the results of io.fits.open() configured using CRDS environment settings,  overriden by
    any conflicting keyword parameter values.
    """
    keys = dict(keys)
    if "checksum" not in keys:
        keys["checksum"] = bool(config.FITS_VERIFY_CHECKSUM)
    if "ignore_missing_end" not in keys:
        keys["ignore_missing_end"] = bool(config.FITS_IGNORE_MISSING_END)
    handle = None
    try:
        handle = fits.open(filename, **keys)
        yield handle
    finally:
        if handle is not None:
            handle.close()

@hijack_warnings
def fits_open_trapped(filename, **keys):
    """Same as fits_open but with some astropy and JWST DM warnings hijacked by CRDS."""
    return fits_open(filename, **keys)

def get_fits_header_union(filepath, needed_keys=(), original_name=None, observatory=None):
    """Get the union of keywords from all header extensions of FITS
    file `fname`.  In the case of collisions, keep the first value
    found as extensions are loaded in numerical order.
    """
    file_obj = FitsFile(filepath)
    header = file_obj.get_header(needed_keys)
    log.verbose("Header of", repr(filepath), "=", log.PP(header), verbosity=90)
    return header

# ============================================================================

class FitsFile(AbstractFile):
    
    format = "FITS"

    def get_info(self):
        """Capture the output from the fits info() function."""
        s = python23.StringIO()
        fits.info(self.filepath, s)
        s.seek(0)
        info_string = "\n".join(s.read().splitlines()[1:])
        return info_string

    def get_format(self, array_name, array_id_info):
        """Return the ArrayInfo object defining the data array `array_name` taken from
        FITS `filepath`
        """
        with fits_open(self.filepath) as hdulist:
            for (i, hdu) in enumerate(hdulist):
                name, class_name, _header_len, shape, typespec, _unknown = hdu._summary()  # XXX uses private _summary
                generic_class = {
                    "IMAGEHDU" : "IMAGE",
                    "BINTABLEHDU" : "TABLE", 
                }.get(class_name.upper(), "UNKNOWN")
                if array_name == name:
                    return ArrayFormat(name, str(i), generic_class, shape, typespec)
        raise 
            
    def get_array(self, name, extension):
        """Return the `name`d array data from `filepath`,  alternately indexed
        by `extension` number.
        """
        with fits_open(self.filepath) as hdus:
            try:
                return hdus[name].data
            except Exception:
                return hdus[extension].data
            
    def get_raw_header(self, needed_keys=()):
        """Get the union of keywords from all header extensions of FITS
        file `fname`.  In the case of collisions, keep the first value
        found as extensions are loaded in numerical order.
        """
        union = []
        with fits_open(self.filepath) as hdulist:
            for hdu in hdulist:
                for card in hdu.header.cards:
                    card.verify('fix')
                    key, value = card.keyword, str(card.value)
                    if not key:
                        continue
                    union.append((key, value))
        return union
    
    def setval(self, key, value):
        fits.setval(self.filepath, key, value=value)

