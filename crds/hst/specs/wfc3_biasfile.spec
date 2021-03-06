{
    'extra_keys': ('subarray',),
    'file_ext': '.fits',
    'filetype': 'bias',
    'ld_tpn': 'wfc3_bia_ld.tpn',
    'parkey': ('DETECTOR', 'CCDAMP', 'CCDGAIN', 'BINAXIS1', 'BINAXIS2', 'APERTURE', 'CHINJECT'),
    'parkey_relevance': {},
    'reffile_format': 'image',
    'reffile_required': 'yes',
    'reffile_switch': 'biascorr',
    'rmap_relevance': '((DETECTOR == "UVIS") and (BIASCORR != "OMIT"))',
    'suffix': 'bia',
    'text_descr': 'Bias Frame',
    'tpn': 'wfc3_bia.tpn',
    'unique_rowkeys': None,
}
