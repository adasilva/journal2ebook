#!/usr/bin/env python
import ImageTk
import PIL.Image
from Tkinter import *
from tkFileDialog import askopenfilename,asksaveasfilename
import tkMessageBox
import os
import re
import pdb
import time
import glob
import subprocess

class Journal2ebook:
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
        self.profileList=[]
        # Some variable initialization
        self.parent=parent
        self.page = 0 
        self.pageString=StringVar()
        self.pageString.set(self.page+1)
        self.maxPages = None
        self.skipFirst = IntVar()
        self.ncols = IntVar()
        self.height = 600      # intended height, also could be set by gui
        self.width = None
        self.img = None
        self.imgaspect = None # aspect ratio of image
        self.filename = None        
        self.filedir = None
        self.configFile = './journal2ebook.conf'
        
        # configuration file
        try:
            f=open(self.configFile,'r')
            self.configVars={line.split(':')[0].replace(' ',''):line.split(':')[1].lstrip().rstrip('\n') for line in f} #dictionary of configuration variables
            f.close()
        except IOError:
            # instead of doing this, maybe the config file should be set up on install?
            self.profileDialog=tkMessageBox.showinfo('Info','No configuration file found.\nA new configuration file has been created for you.')

            file = open(self.configFile, 'w')
            file.write('')
            file.close()

            f=open(self.configFile,'r')
            self.configVars={line.split(':')[0].replace(' ',''):line.split(':')[1].lstrip().rstrip('\n') for line in f} #dictionary of configuration variables
            f.close()
        self.chooseImage()
        try:
            os.mkdir(os.path.join(self.filedir,'tempfiles'))
            self.tempdirexists=False
        except OSError:
            self.tempdirexists=True

        if self.filename=='':
            self.parent.destroy()
        else:
            self.setup()

    def setup(self):
        '''Sets up the main window.'''
        ### Loading and preparing the image. This is done first
        ### because the size of the canvas depends on the image size.
        self.convertImage()
        self.prepImage()

        ### Application uses the grid geometry management
        # currently the size is 5 rows x 4 columns
        
        # Set up a menu bar with Tools.
        self.fMenu=Frame(self.parent, relief='groove')
        self.fMenu.grid(row=0,column=0,columnspan=4)

        self.menubar=Menu(self.parent) #menubar
        self.parent.config(menu=self.menubar) #configuration

        #create one of the menus in the menubar and 
        #add a cascade to contain the tools
        self.tools=Menu(self.menubar)
        self.menubar.add_cascade(label='Tools',menu=self.tools)
        # Add tools to the menu
        self.tools.add_command(label='Save Profile',command=self.saveProfile)
        #self.menubar.add_command(label='Choose Profile')
        self.tools.add_command(label='Exit',command=lambda: self.bQuitClick(None))

        ### Row 1 is the left and right margin scale bars
        self.scale2=Scale(self.parent,from_=0,to=1,orient=HORIZONTAL,resolution=0.01,sliderlength=15,length=self.width/2.+7,showvalue=0)
        self.scale2.grid(row=1,column=1,sticky=W)
        self.scale2.bind('<ButtonRelease-1>',self.drawMargins)
        self.scale2.bind('<KeyRelease-Left>',self.drawMargins)
        self.scale2.bind('<KeyRelease-Right>',self.drawMargins)

        self.scale4=Scale(self.parent,from_=0,to=1,orient=HORIZONTAL,resolution=0.01,sliderlength=15,length=self.width/2.+7,showvalue=0)
        self.scale4.grid(row=1,column=2,sticky=E)
        self.scale4.set(1.)
        self.scale4.bind('<ButtonRelease-1>',self.drawMargins)
        self.scale4.bind('<KeyRelease-Left>',self.drawMargins)
        self.scale4.bind('<KeyRelease-Right>',self.drawMargins)

        ### Columns 0 contains the top and bottom margins
        self.scale1=Scale(self.parent,from_=0,to=1,orient=VERTICAL,resolution=0.01,sliderlength=15,length=self.height/2.+7,showvalue=0)
        self.scale1.grid(row=2,column=0,sticky=NW)
        self.scale1.bind('<ButtonRelease-1>',self.drawMargins)
        self.scale1.bind('<KeyRelease-Up>',self.drawMargins)
        self.scale1.bind('<KeyRelease-Down>',self.drawMargins)

        self.scale3=Scale(self.parent,from_=0,to=1,orient=VERTICAL,resolution=0.01,sliderlength=15,length=self.height/2.+7,showvalue=0)
        self.scale3.grid(row=3,column=0,sticky=SW)
        self.scale3.set(1.)
        self.scale3.bind('<ButtonRelease-1>',self.drawMargins)
        self.scale3.bind('<KeyRelease-Up>',self.drawMargins)
        self.scale3.bind('<KeyRelease-Down>',self.drawMargins)

        ### The canvas to show the image and margin lines spans 4 grid segments
        self.canvas1=Canvas(self.parent,width=self.width,height=self.height)   
        self.canvas1.grid(row=2,column=1,columnspan=2,rowspan=2,sticky=NW,padx=7,pady=7)

        ### Draw the pdf on the canvas        
        # Display image
        self.drawImage()

        ### Draw margin lines - default are at the edges of the image
        self.left=self.canvas1.create_line(0,0,0,self.height)
        self.right=self.canvas1.create_line(self.width,0,self.width,self.height)
        self.top=self.canvas1.create_line(0,0,0,self.width)
        self.bottom=self.canvas1.create_line(0,self.height,self.width,self.height)
        
        ### Create a frame on the side for extras
        self.fExtras=Frame(self.parent)
        self.fExtras.grid(row=2,column=3,sticky=N+S)

        ### Some extra options in last column
        self.bSkipFirst=Checkbutton(self.fExtras,text='Skip first page',variable=self.skipFirst)
        self.bSkipFirst.grid(row=0,column=0,sticky=NW)

        self.bXtracols=Checkbutton(self.fExtras,text='3 or 4 columns',variable=self.ncols)
        self.bXtracols.grid(row=1,column=0,sticky=NW)

        ### Profiles list box
        self.lProfiles=Listbox(self.fExtras)
        self.lProfiles.grid(row=2,column=0,sticky=SW)
        self.lProfiles.bind('<<ListboxSelect>>',self.chooseProfile)

        if 'profiles' in self.configVars and self.configVars['profiles']!='None':
            f=open(self.configVars['profiles'],'r')
            for line in f:
                item=line.strip(']').strip('[').strip('\n').split(',')
                self.profileList.append(item)
            f.close()

        for i in range(len(self.profileList)):
            self.lProfiles.insert(END,self.profileList[i][0])


        ### Quit and save buttons on the side
        self.fButtons=Frame(self.parent)
        self.fButtons.grid(row=3,column=3,sticky=S)
        self.bNewFile=Button(self.fButtons, text='new file',background='#8C99DF')
        self.bNewFile.grid(row=0,column=0,sticky=E+W)
        self.bNewFile.bind('<Button-1>',self.bNewFileClick)
        self.bNewFile.bind('<Return>',self.bNewFileClick)

        self.bReady=Button(self.fButtons, text='Ready!', background='#8C99DF')
        self.bReady.grid(row=1,column=0,sticky=E+W)
        self.bReady.focus_force()  #Force focus to be on button1 on start
        self.bReady.bind('<Button-1>',self.bReadyClick)
        self.bReady.bind('<Return>',self.bReadyClick)
        
        self.bQuit=Button(self.fButtons)
        self.bQuit.configure(text='Quit',background='#8C99DF')
        self.bQuit.grid(row=2,column=0,sticky=E+W)
        self.bQuit.bind('<Button-1>',self.bQuitClick)
        self.bQuit.bind('<Return>',self.bQuitClick)

        ### Page increment buttons within a frame (for centering purposes)
        self.fPageChange=Frame(self.parent)
        self.fPageChange.grid(row=4,column=1,columnspan=2)

        self.bDec=Button(self.fPageChange)
        self.bDec.configure(text='<',background='blue')
        self.bDec.grid(row=0,column=0, sticky=W)
        self.bDec.bind('<Button-1>', self.bDecClick)
        
        self.pageEntry = Entry(self.fPageChange,textvariable=self.pageString,width=4)
        self.pageEntry.grid(row=0,column=1)
        self.pageEntry.bind('<Return>',self.updateImage)

        self.bInc=Button(self.fPageChange)
        self.bInc.configure(text='>',background='blue')
        self.bInc.grid(row=0,column=2, sticky=E)
        self.bInc.bind('<Button-1>', self.bIncClick)

    def chooseImage(self):
        if 'last_dir' in self.configVars and self.configVars['last_dir'] is not '':
            initdir = self.configVars['last_dir']+"/"
        else:
            initdir = '~/'
        self.filename = askopenfilename(parent=self.parent,initialdir=initdir, filetypes=[('pdf','*.pdf'),])
        self.filedir=os.path.dirname(self.filename) #directory
        self.filename=self.filename.rstrip('pdf')
        self.filename=self.filename.rstrip('.') #need to do the two strips separately so that we can handle a file named mypdf.pdf, for example        
        if self.filedir:            
            self.configVars['last_dir'] = self.filedir
            self.saveConfig()

    def convertImage(self):
        # First, convert pdf to png
        imFile=os.path.join(self.filedir,'tempfiles','temp.png')
        subprocess.call(['convert', self.filename+'.pdf', imFile])
        files = [f for f in glob.glob(os.path.join(self.filedir,'tempfiles','*.png')) if re.match('temp-',os.path.basename(f))]
        self.maxPages = len(files)
        
    def prepImage(self):
        # Resize the image
        imFileName='temp-%s.png' % self.page
        imFile=os.path.join(self.filedir,'tempfiles',imFileName)
        try:
            self.img = PIL.Image.open(imFile)
        except IOError:
            try:
                self.img = PIL.Image.open(os.path.join(self.filedir,'tempfiles','temp.png'))
            except IOError as detail:
                print 'Couldn\'t load file: ', detail
        self.imgaspect = float(self.img.size[0]) / float(self.img.size[1])
        self.width = int(self.height * self.imgaspect)
        self.img = self.img.resize((self.width, self.height), PIL.Image.ANTIALIAS)

    def updateImage(self,event):
        if int(self.pageString.get()) > self.maxPages:
            self.pageString.set(self.maxPages)
        elif int(self.pageString.get()) <= 0:
            self.pageString.set(1)            
        self.page = int(self.pageString.get())-1   
        self.prepImage()
        self.canvas1.delete('all')
        self.drawImage()
        #self.drawMargins(event)
        cl=self.scale1.get()*self.height/2.
        self.left=self.canvas1.create_line(0,cl,self.width,cl)
        cr=self.height/2.+self.scale3.get()*self.height/2.
        self.right=self.canvas1.create_line(0,cr,self.width,cr)
        ct=self.scale2.get()*self.width/2.
        self.top=self.canvas1.create_line(ct,0,ct,self.height)
        cb=self.width/2.+self.scale4.get()*self.width/2.
        self.bottom=self.canvas1.create_line(cb,0,cb,self.height)
        
    def drawImage(self):
        self.img=ImageTk.PhotoImage(self.img)
        self.pdfimg=self.canvas1.create_image(self.width/2.,self.height/2.,image=self.img)
        
    def drawMargins(self,event):
        d=7.  #half of the slider length
        g=5   #padding between sliders
        cl=self.scale1.get()*(self.height/2.-d)
        self.canvas1.coords(self.left,0,cl,self.width,cl)
        cr=self.height/2.+d+g+self.scale3.get()*(self.height/2.-d-g)
        self.canvas1.coords(self.right,0,cr,self.width,cr)
        ct=self.scale2.get()*(self.width/2.-d)
        self.canvas1.coords(self.top,ct,0,ct,self.height)
        cb=self.width/2.+d+g+self.scale4.get()*(self.width/2.-d-g)
        self.canvas1.coords(self.bottom,cb,0,cb,self.height)
        
    def cleanUp(self):
        ''' Cleans up temp folder/files that were created. Might be an issue if folder already exists.'''
        files = [f for f in glob.glob(os.path.join(self.filedir,'tempfiles','*.png')) if re.match('temp',os.path.basename(f))]
        for f in files:
            os.remove(f)
        if not self.tempdirexists:
            os.rmdir(os.path.join(self.filedir,'tempfiles'))

    def bDecClick(self,event):
        self.pageString.set(int(self.pageString.get()) - 1)
        self.updateImage(event)
        
    def bIncClick(self,event):    
        self.pageString.set(int(self.pageString.get()) + 1)
        self.updateImage(event)
           
    def bNewFileClick(self,event):
        oldImage=self.filename
        self.chooseImage()  #changes self.filename
        if self.filename==oldImage:
            pass  #don't do anything
        else:
            self.cleanUp()
            self.canvas1.delete('all')
            self.convertImage()
            self.prepImage()
            self.drawImage()
            cl=self.scale1.get()*self.height/2.
            self.left=self.canvas1.create_line(0,cl,self.width,cl)
            cr=self.height/2.+self.scale3.get()*self.height/2.
            self.right=self.canvas1.create_line(0,cr,self.width,cr)
            ct=self.scale2.get()*self.width/2.
            self.top=self.canvas1.create_line(ct,0,ct,self.height)
            cb=self.width/2.+self.scale4.get()*self.width/2.
            self.bottom=self.canvas1.create_line(cb,0,cb,self.height)

    def saveProfile(self):
        if ('profiles' not in self.configVars) or (self.configVars['profiles']=='None'):
            self.setupProfiles()

        self.saveProfileDialog=Toplevel(self.parent)
        profileNameLabel=Label(self.saveProfileDialog,text='Journal name: ')
        profileNameText=StringVar()
        profileNameEntry=Entry(self.saveProfileDialog,width=25,textvariable=profileNameText)
        profileNameLabel.grid(row=0,column=0,sticky=W)
        profileNameEntry.grid(row=1,column=0,sticky=W)
        
        bOK=Button(self.saveProfileDialog)
        bOK.configure(text='OK')
        bOK.focus_force()
        bOK.bind('<Button-1>',lambda event: self.addProfile(profileNameText.get()))
        bOK.bind('<Return>',lambda event: self.addProfile(profileNameText.get()))
        bOK.grid(row=1,column=0,sticky=E)

        bCancel=Button(self.saveProfileDialog)
        bCancel.configure(text='Cancel')
        bCancel.bind('<Button-1>',lambda event: self.saveProfileDialog.destroy())
        bCancel.bind('<Return>',lambda event: self.saveProfileDialog.destroy())
        bCancel.grid(row=2,column=1,sticky=W)
 
    def setupProfiles(self):
        self.profileDialog=Toplevel(self.parent)
        self.fileBoxText=StringVar()
        msg=Message(self.profileDialog,text='This is your first time accessing profiles!\n\nProfiles allow you to save settings that work well for a particular journal or set of journals. \n\nTo begin, select the file in which to save your profile parameters:')
        msg.grid(row=0,column=0,sticky=W)
        fileBox=Entry(self.profileDialog,width=50,textvariable=self.fileBoxText)
        self.fileBoxText.set('./journal2ebook.txt')
        fileBox.grid(row=1,column=0,sticky=W)

        bBrowse=Button(self.profileDialog)
        bBrowse.configure(text='Browse')
        bBrowse.bind('<Button-1>',lambda event:self.fileBoxText.set(asksaveasfilename(parent=self.profileDialog,)))
        bBrowse.bind('<Return>',lambda event:self.fileBoxText.set(asksaveasfilename(parent=self.profileDialog,)))
        bBrowse.grid(row=1,column=1,sticky=W)

        bOK=Button(self.profileDialog)
        bOK.configure(text='OK')
        bOK.focus_force()
        bOK.bind('<Button-1>',self.profilesOK)
        bOK.bind('<Return>',self.profilesOK)
        bOK.grid(row=2,column=0,sticky=E)

        bCancel=Button(self.profileDialog)
        bCancel.configure(text='Cancel')
        bCancel.bind('<Button-1>',lambda event: self.profileDialog.destroy())
        bCancel.bind('<Return>',lambda event: self.profileDialog.destroy())
        bCancel.grid(row=2,column=1,sticky=W)
   
    def profilesOK(self,event):
        self.configVars['profiles'] = self.fileBoxText.get()
        print 'in profilesOK: fileBoxText= %s, configVars=%s' %(self.fileBoxText.get(),self.configVars['profiles'])
        self.saveConfig()
        #need to create the profiles file in stated location
        self.profileDialog.destroy()
        
    def saveConfig(self):
        f=open(self.configFile,'w')
        for item in self.configVars:
            f.write('%s : %s\n' %(str(item),self.configVars[item]))
        f.close()
        
    def addProfile(self,profileName):
        newProfile=[profileName,self.skipFirst.get(),self.ncols.get(),self.scale1.get(),self.scale2.get(),self.scale3.get(),self.scale4.get()]
        self.profileList.append(newProfile)
        f=open(self.configVars['profiles'],'a+') #'a+' to append at the end of file
        profileStr=newProfile[0]
        for i in range(1,len(newProfile)):
            profileStr=profileStr+','+str(newProfile[i])
        f.write(profileStr+'\n')  
        f.close()
        self.lProfiles.insert(END,profileName) 
        self.saveProfileDialog.destroy()

    def chooseProfile(self,event):
        i=int(event.widget.curselection()[0])
        self.skipFirst.set(self.profileList[i][1])
        self.ncols.set(self.profileList[i][2])
        self.scale1.set(self.profileList[i][3])
        self.scale2.set(self.profileList[i][4])
        self.scale3.set(self.profileList[i][5])
        self.scale4.set(self.profileList[i][6])
        self.drawMargins(event)
        
    def bReadyClick(self,event):
        leftmargin=self.scale2.get()*8.5/2.  #convert to inches
        topmargin=self.scale1.get()*11/2.
        bottommargin=(1-self.scale3.get())*11/2.
        rightmargin=(1-self.scale4.get())*8.5/2.
        newFileName=asksaveasfilename(parent=root,filetypes=[('pdf','*.pdf'),('epub','*.epub')] ,title="Save the image as")
        if self.ncols==0:
            n=2
        else:
            n=4
        if self.skipFirst.get()==1:
            npages=len([f for f in glob.glob(os.path.join(self.filedir,'tempfiles','*.png')) if re.match('temp-',os.path.basename(f))])
            pagerange='2-'+str(npages)
            subprocess.call(['k2pdfopt','-x', '-p', pagerange, '-col', str(n), '-ml', str(leftmargin), '-mr', str(rightmargin), '-mt', str(topmargin), '-mb', str(bottommargin), '-ui-','-o',newFileName,'"'+self.filename+'.pdf"'])
        else:
            subprocess.call(['k2pdfopt','-x','-col', str(n), '-ml', str(leftmargin), '-mr', str(rightmargin), '-mt', str(topmargin), '-mb', str(bottommargin), '-ui-','-o', newFileName, '"'+self.filename+'.pdf"'])

    def bQuitClick(self,event):
        self.cleanUp()
        self.parent.destroy()

if __name__ == '__main__':
    root=Tk()
    root.wm_title('journal2ebook')
    myapp=Journal2ebook(root)
    root.mainloop()
