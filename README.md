journal2ebook
=============

Application to convert academic pdfs to epub format for e-readers

Allows you to set margins in a GUI using an image of the first page of
your pdf. The resulting epub file is output to the folder you are
running this app from.

This program works cross-platform (thus far Linux and Windows 7 have
been tested). In all cases, ImageMagick and k2pdfopt must be in the
system's search path.

Requires the following python modules:

Python Imaging Library / ImageTk - to show an image of your pdf in the
application 
You may need to obtain PIL from http://www.pythonware.com/

Tkinter - to make the GUI
This seems to be included with python. 

os - to interface with the operating system
Included with python.

re - For some regex stuff
Included with python.

pdb

glob
   
Also depends on:
imagemagick - to convert pdf to png 
k2pdfopt - to convert pdf to epub