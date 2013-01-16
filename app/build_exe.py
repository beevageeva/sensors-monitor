from distutils.core import setup
import py2exe

import matplotlib

setup(
    console=['app.py'],
    options={
             'py2exe': {
                        'packages' : ['matplotlib', 'pytz'],
                        'excludes' : ['_gtkagg', '_tkagg', 'bsddb', 'curses', 'email', 'pywin.debugger',
            'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl',
            'Tkconstants', 'Tkinter'],
                        'dll_excludes' : ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll', 'tcl84.dll',
                'tk84.dll', 'libgdk_pixbuf-2.0-0.dll']


                       }
            },
    data_files=matplotlib.get_py2exe_datafiles()
)
