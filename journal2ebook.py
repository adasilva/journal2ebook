import ImageTk
import PIL.Image
from Tkinter import *
from tkFileDialog import askopenfilename
import os
import re
import pdb
import time
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
    def __init__(self,parent):

        # Some variable initialization
        self.parent=parent
        self.page = 1        # page of interest, should be set by gui later
        self.skipFirst = IntVar()
        self.height = 600      # intended height, also could be set by gui
        self.width = None
        self.img = None
        self.imgaspect = None # aspect ration of image    
        self.filename=self.chooseImage()
        self.filename=self.filename.rstrip('pdf')
        self.filename=self.filename.rstrip('.') #need to do the two strips separately so that we can handle a file named mypdf.pdf, for example
        # can't handle docs with spaces

        if self.filename=='':
            self.parent.destroy()
        else:
            self.setup()

    def setup(self):
        '''Sets up the main window.'''
        ### Loading and preparing the image. This is done first
        ### because the size of the canvas depends on the image size.
        self.prepImage()
        
        ### Application uses the grid geometry management
        # currently the size is 6 rows x 5 columns

        ### Row 0 is the left and right margin scale bars
        self.scale2=Scale(self.parent,from_=0,to=1,orient=HORIZONTAL,resolution=0.01,sliderlength=15,length=self.width/2.)
        self.scale2.grid(row=0,column=1,columnspan=2,sticky=W)
        self.scale2.bind('<ButtonRelease-1>',self.drawMargins)
        self.scale2.bind('<KeyRelease-Left>',self.drawMargins)
        self.scale2.bind('<KeyRelease-Right>',self.drawMargins)

        self.scale4=Scale(self.parent,from_=0,to=1,orient=HORIZONTAL,resolution=0.01,sliderlength=15,length=self.width/2.,showvalue=1.)
        self.scale4.grid(row=0,column=3,columnspan=2,sticky=E)
        self.scale4.set(1.)
        self.scale4.bind('<ButtonRelease-1>',self.drawMargins)
        self.scale4.bind('<KeyRelease-Left>',self.drawMargins)
        self.scale4.bind('<KeyRelease-Right>',self.drawMargins)

        ### Columns 0 contains the top and bottom margins
        self.scale1=Scale(self.parent,from_=0,to=1,orient=VERTICAL,resolution=0.01,sliderlength=15,length=self.height/2.)
        self.scale1.grid(row=1,column=0,sticky=NW)
        self.scale1.bind('<ButtonRelease-1>',self.drawMargins)
        self.scale1.bind('<KeyRelease-Up>',self.drawMargins)
        self.scale1.bind('<KeyRelease-Down>',self.drawMargins)

        self.scale3=Scale(self.parent,from_=0,to=1,orient=VERTICAL,resolution=0.01,sliderlength=15,length=self.height/2.)
        self.scale3.grid(row=3,column=0,sticky=SW)
        self.scale3.set(1.)
        self.scale3.bind('<ButtonRelease-1>',self.drawMargins)
        self.scale3.bind('<KeyRelease-Up>',self.drawMargins)
        self.scale3.bind('<KeyRelease-Down>',self.drawMargins)

        ### The canvas to show the image and margin lines spans 4 grid segments
        self.canvas1=Canvas(self.parent,width=self.width,height=self.height)   
        self.canvas1.grid(row=1,column=1,columnspan=4,rowspan=4)

        ### Draw the pdf on the canvas        
        # Display image
        self.img=ImageTk.PhotoImage(self.img)
        self.pdfimg=self.canvas1.create_image(self.width/2.,self.height/2.,image=self.img)

        ### Draw margin lines - default are at the edges of the image
        self.left=self.canvas1.create_line(0,0,0,self.height)
        self.right=self.canvas1.create_line(self.width,0,self.width,self.height)
        self.top=self.canvas1.create_line(0,0,0,self.width)
        self.bottom=self.canvas1.create_line(0,self.height,self.width,self.height)
        
        ### Some extra options in last column
        self.bSkipFirst=Checkbutton(self.parent,text='Skip first page',variable=self.skipFirst)
        self.bSkipFirst.grid(row=1,column=5,sticky=NW)

        ### Quit and save buttons in the bottom row
        self.bNewFile=Button(self.parent, text='new file')
        self.bNewFile.grid(row=5,column=0,sticky=W)
        self.bNewFile.bind('<Button-1>',self.bNewFileClick)
        self.bNewFile.bind('<Return>',self.bNewFileClick)

        self.bReady=Button(self.parent, text='ready!', background='green')
        self.bReady.grid(row=5,column=4,sticky=E)
        self.bReady.focus_force()  #Force focus to be on button1 on start
        self.bReady.bind('<Button-1>',self.bReadyClick)
        self.bReady.bind('<Return>',self.bReadyClick)
        
        self.bQuit=Button(self.parent)
        self.bQuit.configure(text='quit',background='red')
        self.bQuit.grid(row=5,column=5,sticky=E)
        self.bQuit.bind('<Button-1>',self.bQuitClick)
        self.bQuit.bind('<Return>',self.bQuitClick)

    def chooseImage(self):
        filename = askopenfilename(parent=self.parent,initialdir='~/', filetypes=[("pdf","*.pdf"),])
        return filename

    def prepImage(self):
        # First, convert pdf to png
        t1=time.time()
        os.system('convert %s.pdf temp.png' % self.filename)
        print 'convert to pdf took ', time.time()-t1, ' s'
        # Resize the image
        self.img = PIL.Image.open('temp-%s.png' % self.page)
        self.imgaspect = float(self.img.size[0]) / float(self.img.size[1])        
        self.width = int(self.height * self.imgaspect)
        t1=time.time()
        self.img = self.img.resize((self.width, self.height), PIL.Image.ANTIALIAS)
        print 'resize took ', time.time()-t1, ' s'

    def drawMargins(self,event):
        cl=self.scale1.get()*self.height/2.
        self.canvas1.coords(self.left,0,cl,self.width,cl)
        cr=self.height/2.+self.scale3.get()*self.height/2.
        self.canvas1.coords(self.right,0,cr,self.width,cr)
        ct=self.scale2.get()*self.width/2.
        self.canvas1.coords(self.top,ct,0,ct,self.height)
        cb=self.width/2.+self.scale4.get()*self.width/2.
        self.canvas1.coords(self.bottom,cb,0,cb,self.height)
       
    def cleanUp(self):
        ''' Cleans up temp files that were created. A more elegant way
        to do this might be to create a temp folder and remove the
        entire folder afterwards.'''
        files = [f for f in glob.glob("*.png") if re.match('temp-',f)]
        
        for f in files:
            os.remove(f)

    def bNewFileClick(self,event):
        self.filename=self.chooseImage()
        self.filename=self.filename.rstrip('pdf')
        self.filename=self.filename.rstrip('.') #need to do the two strips separately so that we can handle a file named mypdf.pdf, for example
        if self.filename=='':
            self.parent.destroy()
        else:
            self.cleanUp()
            self.canvas1.delete('all')
            self.prepImage()
            self.img=ImageTk.PhotoImage(self.img)
            self.pdfimg=self.canvas1.create_image(self.width/2.,self.height/2.,image=self.img)
            cl=self.scale1.get()*self.height/2.
            self.canvas1.coords(self.left,0,cl,self.width,cl)
            cr=self.height/2.+self.scale3.get()*self.height/2.
            self.canvas1.coords(self.right,0,cr,self.width,cr)
            ct=self.scale2.get()*self.width/2.
            self.canvas1.coords(self.top,ct,0,ct,self.height)
            cb=self.width/2.+self.scale4.get()*self.width/2.
            self.canvas1.coords(self.bottom,cb,0,cb,self.height)

            self.left=self.canvas1.create_line(cl)
            self.right=self.canvas1.create_line(cr)
            self.top=self.canvas1.create_line(ct)
            self.bottom=self.canvas1.create_line(cb)

    def bReadyClick(self,event):
        leftmargin=self.scale2.get()*8.5/2.  #convert to inches
        topmargin=self.scale1.get()*11/2.
        bottommargin=(1-self.scale3.get())*11/2.
        rightmargin=(1-self.scale4.get())*8.5/2.
        if self.skipFirst.get()==1:
            npages=len([f for f in glob.glob("*.png") if re.match('temp-',f)])
            pagerange='2-'+str(npages)
            os.system('k2pdfopt -x -p %s -ml %s -mr %s -mt %s -mb %s -ui- %s.pdf' %(pagerange,leftmargin,rightmargin,topmargin,bottommargin,self.filename)) 
        else:
            os.system('k2pdfopt -x -ml %s -mr %s -mt %s -mb %s -ui- %s.pdf' %(leftmargin,rightmargin,topmargin,bottommargin,self.filename)) 

    def bQuitClick(self,event):
        self.cleanUp()
        self.parent.destroy()


if __name__ == '__main__':
    root=Tk()
    root.wm_title('journal2ebook')
    myapp=MyApp(root)#,'~/Downloads/1210.3282v1.pdf')
    #myapp=MyApp(root,'~/Downloads/1210.3282v1.pdf')#filename)
    #myapp=MyApp(root,'C:\\Users\\Jason\\Desktop\\sk2006.pdf')#filename)
    root.mainloop()
