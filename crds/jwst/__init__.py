from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
import os.path

from crds import reftypes

HERE  = os.path.dirname(__file__) or "."

TYPES = reftypes.from_package_file(__file__)

INSTRUMENTS = TYPES.instruments
EXTENSIONS = TYPES.extensions
TEXT_DESCR = TYPES.text_descr
FILEKINDS = TYPES.filekinds

UNDEFINED_PARKEY_SUBST_VALUE = "N/A"

INSTRUMENT_FIXERS = {
}

TYPE_FIXERS = {
}

PROVENANCE_KEYWORDS = ("DESCRIP", "PEDIGREE", "USEAFTER","HISTORY", "AUTHOR")


