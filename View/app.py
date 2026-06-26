import customtkinter as ctk
import threading
import TextListener
import queue
from queue import Queue

import time

class innerLeftFrame(ctk.CTkFrame):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,**kwargs)
        self.grid_propagate(False)



class LeftFrame(ctk.CTkFrame):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,**kwargs)

        self.grid_propagate(False)

        self.grid_rowconfigure(0,weight=0)
        self.grid_rowconfigure(1,weight=2)
        self.grid_columnconfigure(0,weight=1)
        self.TextLabel = ctk.CTkLabel(self,font=("Helvetica",20,"bold"))
        self.TextLabel.grid(row = 0,column = 0,padx = 20, pady=20,sticky ="n")
        self.TextLabel.configure(text="LECRec")

        self.innerFrame = innerLeftFrame(self,width=200)
        self.innerFrame.grid(row = 1,column = 0,padx = 20, pady=20,sticky="ns")
    

class RightFrame(ctk.CTkFrame):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,**kwargs)

        self.grid_propagate(False)



class BottomFrame(ctk.CTkFrame):
     

    def __init__(self,parent,TextBox,**kwargs):
        super().__init__(parent,**kwargs)
        self.audioQueue = Queue()
        self.TextBoxQueueIn = Queue()
        self.TextBoxQueueOut = Queue()
        self.Buttons()
        self.TextBox = TextBox
        self.isPause = threading.Event()
        self.BreakCheck = False
        self.STTEngine = None
        self.SummaryEngine = None
        self.exit_signal = None
        self.check()

    def Play(self):
        if self.isPause.is_set():
            self.isPause.clear()
        else:
            self.exit_signal = threading.Event()
            self.STTEngine = threading.Thread(
                target=TextListener.AudioListener,
                args=(self.audioQueue,self.exit_signal,self.isPause),
                daemon=True)
            self.STTEngine.start()
            self.BreakCheck = False

    def Pause(self):
        if self.isPause.is_set():
            self.isPause.clear()
        else:
            self.isPause.set()

    def Stop(self):
        self.exit_signal.set()
        print("Oh i am putting the text in :)")
        self.TextBoxQueueIn.put(self.TextBox.get("1.0","end-1c"))
        self.SummaryEngine = threading.Thread(
            target = TextListener.LLMSummerizer,
            args=(self.TextBoxQueueIn,self.TextBoxQueueOut,),
            daemon=True
        )
        self.SummaryEngine.start()
        self.GetSummary()


    def GetSummary(self):
        try:
            while True:
                SummaryText = self.TextBoxQueueOut.get_nowait()
                print("Oh Hey A response")
                self.TextBox.configure(state="normal")
                self.TextBox.delete("0.0","end")
                self.TextBox.insert("end-1c",SummaryText)
                self.TextBox.configure(state="disabled")
                self.BreakCheck = True

        except queue.Empty:
            pass

        finally:

            if not self.BreakCheck:
                self.after(10,self.GetSummary)
            else:
                print("Oh hey I am Stopping :)")







    def check(self):
        try:
           while True:
               text = self.audioQueue.get_nowait()
               self.audioQueue.task_done()
               if text is True:
                    
                    self.TextBox.configure(state="normal") 
               elif text is False:
                    self.TextBox.configure(state="disabled")
               else:
                    
                    self.TextBox.configure(state="normal")
                    self.TextBox.insert("end-1c",text)
                    self.TextBox.configure(state="disabled")
                    self.TextBox.see("end")
        except queue.Empty:
           pass
        finally:
            self.after(10,self.check)


    def Buttons(self):

        self.grid_propagate(False)
        self.pack_propagate(False)

        
        self.play = ctk.CTkButton(self,width=200,text="Play" ,command=self.Play)
        self.pause = ctk.CTkButton(self,width=200,text="Pause",command= self.Pause)
        self.stop =ctk.CTkButton(self,width=200,text="Stop", command = self.Stop)
        self.grid_columnconfigure(0,weight=1)
        self.grid_columnconfigure(1,weight=1)
        self.grid_columnconfigure(2,weight=1)
        self.grid_rowconfigure(1,weight=1)

        self.play.grid(row=1,column=0,padx=20,pady=20,sticky="ns")
        self.pause.grid(row=1,column=1,padx=20,pady=20,sticky="ns")
        self.stop.grid(row=1,column=2,padx=20,pady=20,sticky="ns")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()


        self.title("LECRec")
        self.geometry("1200x700")


        self.leftFrame_1 = LeftFrame(self,width=250)
        self.leftFrame_1.pack(side="left",padx=10,pady=10,fill='y',expand=False)

        self.rightFrame_1 = RightFrame(self,width=250)
        self.rightFrame_1.pack(side="right",padx=10,pady=10,fill='y',expand=False)

       

        self.textBox = ctk.CTkTextbox(self,width=700,height=450)
        self.textBox.pack(side="top",padx=10,pady=10)
        self.textBox.configure(state="disabled")





        self.bottomFrame_1= BottomFrame(self,self.textBox,width = 700,height=125)
        self.bottomFrame_1.pack(side="bottom",padx=10,pady=10)




        


app = App()
app.mainloop()