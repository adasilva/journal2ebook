journal2ebook
=============

Graphical application to convert academic pdfs to epub format for
e-readers using k2pdfopt as a backend.

The GUI allows you to visualize your PDF and draw appropriate margins
that will be passed to k2pdfopt. The resulting pdf file is output to
the folder of your choice. There is also functionality to save and
recall journal profiles that store margin values.

This program should work cross-platform (Linux, Mac, and Windows) though it has been most extensively tested with Linux. The Windows executable is usually behind in features, but is the most recent version that has been tested in Windows. We do not currently test on Mac.

The dependencies listed in the following sections must also be met.

All users
---------
* Python 2.6 or higher

Third party programs as backends:

* To convert pdf to png:
  * imagemagick for linux and windows users
  * sipe for mac users
* k2pdfopt - to convert pdf to epub
* ImageMagick and k2pdfopt must be in your system's search PATH (or installed in the journal2ebook directory)


Linux / Mac Users
-----------------
Non-standard python modules needed:

* Python Imaging Library / ImageTk - to show an image of your pdf in
the application

  You may need to obtain PIL from http://www.pythonware.com/

To install:

* Download the src directory

* From within the src directory, type into the command line

  sudo python setup.py install

* You can now use the application by typing journal2ebook in the command line (with or without a filename argument) 

You can try this software without installing:

* Double click on journal2ebook.py 

  (if it doesn't work, check that the file is executable)

* Run from the terminal: 

  python journal2ebook.py


Windows
-------
* Python Imaging Library / ImageTk - to show an image of your pdf in
the application

  You may need to obtain PIL from http://www.pythonware.com/

* ghostscript - to convert pdf to png

  (http://sourceforge.net/projects/ghostscript/)


Dependencies that seem to be included with most installations of python:
------------------------------------------------------------------------

* Tkinter - to make the GUI
* os - to interface with the operating system
* re - For some regex stuff
* pdb
* time
* glob
* subprocess
  
