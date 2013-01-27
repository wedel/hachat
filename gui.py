'''this is the module for the GUI'''

import const
import Tkinter
import ScrolledText
import Queue
import logging

CODEC = 'utf8'

class gui(object):
    '''GUI Class for Hachat User Interface'''
    def __init__(self, parent):
        self.root = Tkinter.Tk()
        self.root.title('HaChat v' + str(const.HACHAT_VERSION) + ': ' + parent.name)
        self.parent = parent
        
        #Queue
        self.queue = Queue.Queue()
        self.root.after(50, self.check_queue)
        
        self.stop = False
                
        self.fpopup = Tkinter.Frame(self.root, width=500) 
        self.fpopup.pack(expand=1, fill=ScrolledText.BOTH) 

        self.textfenster = ScrolledText.ScrolledText(self.fpopup, width=90, height=24, background='white')
        self.textfenster.pack(fill=ScrolledText.BOTH, expand='YES')
    
        self.eingabe = Tkinter.Entry(self.fpopup, width=60, background='white')
        self.eingabe.pack(side=ScrolledText.LEFT, fill=ScrolledText.BOTH, expand='YES')

        ## Bindings . . .
        self.eingabe.bind('<Return>', self.senden_)
        self.eingabe.bind('<F1>', self.senden_)

        ## Buttons    
        self.but2 = Tkinter.Button(self.fpopup, text='Senden', command=self.senden)
        self.but2.pack(side = ScrolledText.LEFT, expand='NO')

        self.but3 = Tkinter.Button(self.fpopup, text='Beenden', command=self.ende)
        self.but3.pack(side = ScrolledText.LEFT, expand='NO')


    def run(self):
        '''start gui'''              
        logging.debug("gui starting...")
        self.root.mainloop()
        
    def check_queue(self):
        '''resieve a txt-msg and push it in the gui
        uses a Queue which is checked every 50ms'''
        try:
            msg = self.queue.get(block=False)
        except Queue.Empty:
            pass
        else:
            self.textfenster.insert(Tkinter.END, msg.name+": "+msg.text+'\n')
            self.textfenster.see(Tkinter.END)
        self.root.after(50, self.check_queue)   
        
    def ende_(self, event):
        '''event: calls ende() to stop gui and hachat'''
        self.ende()

    def ende(self):
        '''stops hachat and gui'''
        self.stop = True
        logging.debug("Quitting...")
        self.root.destroy()

    def senden_(self, event):
        '''event: calls senden() to send a txt-msg from the gui'''
        self.senden()
        
    def senden(self):
        '''send a txt-msg from the gui'''
        msg = self.eingabe.get().encode(CODEC)
        self.textfenster.insert(Tkinter.END, self.parent.name+": "+msg+'\n')
        self.textfenster.see(Tkinter.END)    
        self.eingabe.delete('0', Tkinter.END)
        self.eingabe.focus_set()
        self.parent.sendText(msg) #ruft sendText() aus Peer
