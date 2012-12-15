from Tkinter import *
from ScrolledText import *
import tkMessageBox
import tkSimpleDialog
import time
import logging
import threading 

class gui(object):
    
    def __init__(self, parent):
        self.root = Tk()
        self.root.title('HaChat v0.1')
        self.parent = parent
                
        self.fpopup = Frame(self.root,width=500) 
        self.fpopup.pack(expand=1, fill=BOTH) 
 
        self.popup = Menu(self.fpopup,tearoff=0)
        self.popup.add_command(label='Beenden', command= self.ende )


        self.textfenster = ScrolledText(self.fpopup,width=90,height=24,background='white')
        self.textfenster.pack(fill=BOTH,expand=YES)
    
        self.eingabe = Entry(self.fpopup,width=60,background='white')
        self.eingabe.pack(side=LEFT,fill=BOTH,expand=YES)

        ## Bindings . . .
        self.eingabe.bind('<Return>',self.senden_)
        self.eingabe.bind('<F1>',self.senden_)
        self.textfenster.bind('<Button-3>',self.popup_)

        ## Buttons    
        self.but2 = Button(self.fpopup,text='Senden', command = self.senden)
        self.but2.pack(side = LEFT,expand=NO)

        self.but3 = Button(self.fpopup,text='Beenden', command = self.ende)
        self.but3.pack(side = LEFT,expand=NO)


    def run(self):
        ## gui starten...              
        logging.debug("gui starting")
        self.guiRunThread = threading.Thread(target=self.root.mainloop())
        self.guiRunThread.daemon = True
        self.guiRunThread.start()
        
    def ende_(self, event):
        self.ende()

    def ende(self):
        logging.debug("Quitting...")
        self.root.destroy()

    def senden_(self, event):
        self.senden()
        
    def senden(self):
        msg = self.eingabe.get()
        self.textfenster.insert(END,self.parent.name+": "+msg+'\n')
        self.textfenster.see(END)    
        self.eingabe.delete('0',END)
        self.eingabe.focus_set()
        self.parent.sendText(msg) #ruft sendText() aus Peer
    
    def empfang(self,msg):
        self.textfenster.insert(END,msg.name+": "+msg.text+'\n')
        self.textfenster.see(END)  
        
    def popup_(self, event):     
        self.popup.post(event.x_root, event.y_root)
