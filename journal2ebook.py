import ImageTk
import PIL.Image
from Tkinter import *
import os

import pdb

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
        self.page = 2        # page of interest, should be set by gui later
        self.height=600      # intended height, also could be set by gui       
        self.myParent=parent
        
        ### Loading and preparing the image. This is done first
        ### because the size of the canvas depends on the image size.
        # First, convert pdf to png
        self.filename=filename.rstrip('pdf')
        self.filename=self.filename.rstrip('.')
        os.system('convert %s.pdf temp.png' % self.filename)
        
        # Resize the image
        self.img = PIL.Image.open('temp-%s.png' % self.page)
        self.imgaspect = float(self.img.size[0]) / float(self.img.size[1])        
        self.width = int(self.height * self.imgaspect)
        self.img = self.img.resize((self.width, self.height), PIL.Image.ANTIALIAS)

        ### Top frame is the left and right margin scale bars
        self.frame1=Frame(parent)
        self.frame1.pack()

        self.scale2=Scale(self.frame1,from_=0,to=1,orient=HORIZONTAL,resolution=0.01,sliderlength=15,label='left margin')
        self.scale2.pack(side=LEFT)
        self.scale2.bind('<ButtonRelease-1>',self.drawMargins)

        self.scale4=Scale(self.frame1,from_=0,to=1,orient=HORIZONTAL,resolution=0.01,sliderlength=15,label='right margin')
        self.scale4.pack(side=LEFT)
        self.scale4.bind('<ButtonRelease-1>',self.drawMargins)

        ### Below these are the top and bottom margins
        #self.frame2=Frame(parent)
        #self.frame2.pack()
 
        self.scale1=Scale(self.frame1,from_=0,to=1,orient=VERTICAL,resolution=0.01,sliderlength=15,label='top margin')
        self.scale1.pack(side=LEFT)
        self.scale1.bind('<ButtonRelease-1>',self.drawMargins)

        self.scale3=Scale(self.frame1,from_=0,to=1,orient=VERTICAL,resolution=0.01,sliderlength=15,label='bottom margin')
        self.scale3.pack(side=LEFT)
        self.scale3.bind('<ButtonRelease-1>',self.drawMargins)

        ### Below this is the canvas to show the image and margin lines
        self.canvas1=Canvas(parent,width=self.width,height=self.height)   
        self.canvas1.pack()

        ### Draw the pdf on the canvas        
        # Display image
        self.img=ImageTk.PhotoImage(self.img)
        self.pdfimg=self.canvas1.create_image(self.width/2.,self.height/2.,image=self.img) #need to choose image (getimage button?)

        ### Draw margin lines - default are at the edges of the image
        self.left=self.canvas1.create_line(0,0,0,self.height)
        self.right=self.canvas1.create_line(self.width,0,self.width,self.height)
        self.top=self.canvas1.create_line(0,0,0,self.width)
        self.bottom=self.canvas1.create_line(0,self.height,self.width,self.height)

        ### Quit and save buttons
        self.frame3=Frame(parent)
        self.frame3.pack()
        self.bReady=Button(self.frame3, text='ready!', background='green')
        self.bReady.pack(side=LEFT)
        self.bReady.focus_force()  #Force focus to be on button1 on start
        self.bReady.bind('<Button-1>',self.bReadyClick)
        self.bReady.bind('<Return>',self.bReadyClick)
        
        self.bQuit=Button(self.frame3)
        self.bQuit.configure(text='quit',background='red')
        self.bQuit.pack(side=RIGHT)
        self.bQuit.bind('<Button-1>',self.bQuitClick)
        self.bQuit.bind('<Return>',self.bQuitClick)

    def bReadyClick(self,event):
        leftmargin=self.scale2.get()*8.5/2.  #convert to inches
        topmargin=self.scale1.get()*11/2.
        bottommargin=(1-self.scale3.get())*11/2.
        rightmargin=(1-self.scale4.get())*8.5/2.
        os.system('k2pdfopt -ml %s -mr %s -mt %s -mb %s %s.pdf' %(leftmargin,rightmargin,topmargin,bottommargin,self.filename)) 

    def bQuitClick(self,event):
        self.myParent.destroy()

    def drawMargins(self,event):
        cl=self.scale1.get()*self.height/2.
        self.canvas1.coords(self.left,0,cl,self.width,cl)
        cr=self.height/2.+self.scale3.get()*self.height/2.
        self.canvas1.coords(self.right,0,cr,self.width,cr)
        ct=self.scale2.get()*self.width/2.
        self.canvas1.coords(self.top,ct,0,ct,self.height)
        cb=self.width/2.+self.scale4.get()*self.width/2.
        self.canvas1.coords(self.bottom,cb,0,cb,self.height)

if __name__ == '__main__':
    #pdb.set_trace()
    
    root=Tk()
    myapp=MyApp(root,'~/Downloads/13670050308667769.pdf')#filename)
    root.mainloop()
    
    
    #canvas - container for drawing
    #frame - most frequently used container
