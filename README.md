journal2ebook
=============

Graphical application to convert academic pdfs to epub format for
e-readers using k2pdfopt as a backend.

The GUI allows you to visualize your PDF and draw appropriate margins
that will be passed to k2pdfopt. The resulting pdf file is output to
the folder of your choice. There is also functionality to save and
recall journal profiles that store margin values.

This program should work cross-platform (Linux, Mac, and Windows;
though it has been most extensively tested with Linux). In any case,
ImageMagick and k2pdfopt must be in your system's search PATH (or
installed ot the journal2ebook directory). The dependencies listed in the folloing sections must also be met.

Linux / Mac Users
-----------------
Non-standard python modules needed:

* Python Imaging Library / ImageTk - to show an image of your pdf in
the application

  You may need to obtain PIL from http://www.pythonware.com/

Third party programs as backends:

* imagemagick - to convert pdf to png 
* k2pdfopt - to convert pdf to epub

Two ways to run this software:

* Double click on journal2ebook.py (if it doesn't work, check that the file is executable)
* Run from the terminal: python journal2ebook.py


Windows
-------
* Python Imaging Library / ImageTk - to show an image of your pdf in
the application

  You may need to obtain PIL from http://www.pythonware.com/

*ghostscript - to convert pdf to png

  (http://sourceforge.net/projects/ghostscript/)

Third party programs as backends:

* imagemagick - to convert pdf to png 
* k2pdfopt - to convert pdf to epub



Dependencies that seem to be included with most installations of python:
------------------------------------------------------------------------

* Tkinter - to make the GUI
* os - to interface with the operating system
* re - For some regex stuff
* pdb
* time
* glob
* subprocess
  
