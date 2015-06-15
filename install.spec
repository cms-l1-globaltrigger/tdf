# Handling auto bytecompiled python side files created by buildrpm command.
# Prevents a `Installed (but unpackaged) file(s) found' error.

python setup.py install --optimize 1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES.tmp
cat INSTALLED_FILES.tmp > INSTALLED_FILES

# Add .pyc and .pyo files for the all TDF scripts.
for f in `cat INSTALLED_FILES.tmp | grep "etc/routines\|etc/unittest" | grep "\.py"`
do
    echo ${f}c >> INSTALLED_FILES
    echo ${f}o >> INSTALLED_FILES
done
