import ImageTk
import PIL.Image
from Tkinter import *
from tkFileDialog import askopenfilename
import os
import re
import pdb
import glob

class MyApp:
    '''
    Converts a pdf to an epub using the k2pdfopt application
    
    Allows you to set margins in a GUI using an image of the first page of
    your pdf. The resulting epub file is output to the folder you are
    running this app from.
    
    Requires the following python modules:
    ImageTk - to show an image of your pdf in the application
    Tkinter - to make the GUI
    os - to interface with the operating system
    
    Also depends on:
    imagemagick - to convert pdf to png 
    k2pdfopt - to convert pdf to epub
    '''
    def __init__(self,parent,filename):

        # Some variable initialization
        self.page = 2        # page of interest, should be set by gui later
        self.height = 600      # intended height, also could be set by gui
        self.width = None
        self.img = None
        self.imgaspect = None # aspect ration of image      
        self.filename=filename.rstrip('.pdf')

        self.parent=parent
        
        ### Loading and preparing the image. This is done first
        ### because the size of the canvas depends on the image size.
        self.prepImage()
        
        ### Application uses the grid geometry management
        # currently the size is 4 rows x 3 columns

        ### Top row is the left and right margin scale bars
        self.scale2=Scale(self.parent,from_=0,to=1,orient=HORIZONTAL,resolution=0.01,sliderlength=15,label='left margin',length=self.width/2.)
        self.scale2.grid(row=0,column=1,sticky=W)
        self.scale2.bind('<ButtonRelease-1>',self.drawMargins)

        self.scale4=Scale(self.parent,from_=0,to=1,orient=HORIZONTAL,resolution=0.01,sliderlength=15,label='right margin',length=self.width/2.,showvalue=1.)
        self.scale4.grid(row=0,column=2,sticky=E)
        self.scale4.set(1.)
        self.scale4.bind('<ButtonRelease-1>',self.drawMargins)

        ### Column 0 contains the top and bottom margins
        self.scale1=Scale(self.parent,from_=0,to=1,orient=VERTICAL,resolution=0.01,sliderlength=15,label='top margin',length=self.height/2.)
        self.scale1.grid(row=1,column=0,sticky=NW)
        self.scale1.bind('<ButtonRelease-1>',self.drawMargins)

        self.scale3=Scale(self.parent,from_=0,to=1,orient=VERTICAL,resolution=0.01,sliderlength=15,label='bottom margin',length=self.height/2.)
        self.scale3.grid(row=2,column=0,sticky=SW)
        self.scale3.set(1.)
        self.scale3.bind('<ButtonRelease-1>',self.drawMargins)

        ### The canvas to show the image and margin lines spans 4 grid segments
        self.canvas1=Canvas(parent,width=self.width,height=self.height)   
        self.canvas1.grid(row=1,column=1,columnspan=2,rowspan=2)

        ### Draw the pdf on the canvas        
        # Display image
        self.img=ImageTk.PhotoImage(self.img)
        self.pdfimg=self.canvas1.create_image(self.width/2.,self.height/2.,image=self.img) #need to choose image (getimage button?)

        ### Draw margin lines - default are at the edges of the image
        self.left=self.canvas1.create_line(0,0,0,self.height)
        self.right=self.canvas1.create_line(self.width,0,self.width,self.height)
        self.top=self.canvas1.create_line(0,0,0,self.width)
        self.bottom=self.canvas1.create_line(0,self.height,self.width,self.height)

        ### Quit and save buttons in the bottom row
        self.bReady=Button(self.parent, text='ready!', background='green')
        self.bReady.grid(row=3,column=1,sticky=E)
        self.bReady.focus_force()  #Force focus to be on button1 on start
        self.bReady.bind('<Button-1>',self.bReadyClick)
        self.bReady.bind('<Return>',self.bReadyClick)
        
        self.bQuit=Button(self.parent)
        self.bQuit.configure(text='quit',background='red')
        self.bQuit.grid(row=3,column=2,sticky=W)
        self.bQuit.bind('<Button-1>',self.bQuitClick)
        self.bQuit.bind('<Return>',self.bQuitClick)

    def prepImage(self):
        # First, convert pdf to png
        os.system('convert %s.pdf temp.png' % self.filename)
        
        # Resize the image
        self.img = PIL.Image.open('temp-%s.png' % self.page)
        self.imgaspect = float(self.img.size[0]) / float(self.img.size[1])        
        self.width = int(self.height * self.imgaspect)
        self.img = self.img.resize((self.width, self.height), PIL.Image.ANTIALIAS)

    def drawMargins(self,event):
        cl=self.scale1.get()*self.height/2.
        self.canvas1.coords(self.left,0,cl,self.width,cl)
        cr=self.height/2.+self.scale3.get()*self.height/2.
        self.canvas1.coords(self.right,0,cr,self.width,cr)
        ct=self.scale2.get()*self.width/2.
        self.canvas1.coords(self.top,ct,0,ct,self.height)
        cb=self.width/2.+self.scale4.get()*self.width/2.
        self.canvas1.coords(self.bottom,cb,0,cb,self.height)
<<<<<<< HEAD
'''

class FileChooser():
    #gui for choosing file to convert
    def __init__(self,parent):
        self.parent=parent
        ### File browser
        self.frame1=Frame(parent)
        self.filename = tkFileDialog.askopenfilename(filetypes=[("allfiles","*"),("pythonfiles","*.py")])
        ### Quit and save buttons
        self.frame2=Frame(parent)
        self.frame2.pack()
        self.bReady=Button(self.frame2, text='OK')
        self.bReady.pack(side=LEFT)
        self.bReady.focus_force()  #Force focus to be on button1 on start
        self.bReady.bind('<Button-1>',self.bReadyClick)
        self.bReady.bind('<Return>',self.bReadyClick)
        
        self.bQuit=Button(self.frame2)
        self.bQuit.configure(text='Cancel')
        self.bQuit.pack(side=RIGHT)
        self.bQuit.bind('<Button-1>',self.bQuitClick)
        self.bQuit.bind('<Return>',self.bQuitClick)

    def bReadyClick(self,event):
        #Filename chooser.
        self.parent.destroy()

    def bQuitClick(self,event):
        #Quit without choosing a file.
        self.filename = None  #returns no files!
        self.parent.destroy()
'''

def fileChooser():
    root=Tk()
    filename = askopenfilename(initialdir='~/', filetypes=[("pdf","*.pdf"),])
    return filename


if __name__ == '__main__':
    
    filename=fileChooser()

    root=Tk()

    # GUI to select pdf file
    #window1=FileChooser(root)
    #root.mainloop()
    #filename=window1.filename

    #if filename==None:
    #    pass
    #else:

    # Pass filename to myapp & run application
    myapp=MyApp(root,filename)#,'~/Downloads/MoireBands.pdf')#filename)
    root.mainloop()
=======
        
    def cleanUp(self):
        ''' Cleans up temp files that were created. A more elegant way
        to do this might be to create a temp folder and remove the
        entire folder afterwards.'''
        files = [f for f in glob.glob("*.png") if re.match('temp-',f)]
        
        for f in files:
            os.remove(f)

    def bReadyClick(self,event):
        leftmargin=self.scale2.get()*8.5/2.  #convert to inches
        topmargin=self.scale1.get()*11/2.
        bottommargin=(1-self.scale3.get())*11/2.
        rightmargin=(1-self.scale4.get())*8.5/2.
        os.system('k2pdfopt -x -ml %s -mr %s -mt %s -mb %s -ui- %s.pdf' %(leftmargin,rightmargin,topmargin,bottommargin,self.filename)) 

    def bQuitClick(self,event):
        self.cleanUp()
        self.parent.destroy()

if __name__ == '__main__':
    #pdb.set_trace()
    root=Tk()
    myapp=MyApp(root,'~/Downloads/1210.3282v1.pdf')#filename)
    root.mainloop()
    #canvas - container for drawing
    #frame - most frequently used container
>>>>>>> master
