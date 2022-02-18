#D:\dv\python\dist>c:\Python26\python setup.py py2exe
from distutils.core import setup
import py2exe
#setup(console=['cm_app.py','frmCMCell.py','cm_defines.py'])
#py_modules = ['cm_app','frmCMCell','cm_defines']
setup(windows=['cm_app.py'])