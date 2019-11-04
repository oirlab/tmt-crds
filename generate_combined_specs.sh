#! /bin/sh
# CRDS type specifications are configured in code as individual files in the
# project "specs" subdirectories.  This step creates combined versions of the
# specs files for faster loading at runtime by first removing the existing
# combined spec and then invoking the project package.  Importing the project
# packages triggers loading type specs which will automatically rebuild the
# (intentionally removed) combined .json file for faster loading in the future.
# Once the combined .json spec has been generated, it is committed and
# installed as code by setup.py and it will be loaded in preference to the
# individual specs to reduce impact on the file system.  Unless type specifications
# are being modified,  regenerating the comined_specs.json files should have
# no effect.   When types are added or modified,  the combined_specs.json file
# will also automatically be modified during ./install,  and the changes should be
# both committed to GitHub and later installed normally as source code by setup.py.
# (setup.py does not regenerate these combined spec files,  it is assumed that
# type developers will execute this ./install script at least once after adding
# or changing CRDS type specs,  after which the combined spec file is effectively
# source code.

rm crds/tmt/specs/combined_specs.json

find crds/tmt/specs -name '*.rmap' | xargs python -m crds.refactoring.checksum

python -m crds.tmt
