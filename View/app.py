import customtkinter as ctk
import threading
import TextListener
import queue
from queue import Queue
from tkinter import messagebox
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
        self.pack_propagate(False)
        self.textBox = ctk.CTkTextbox(self,width=220,height=500,state="disabled")
        self.textBox.pack(side="top",padx=10,pady=10,expand = False)

        self.QueLabel = ctk.CTkLabel(self,width=220,height=5,text="Ask a Question")
        self.QueLabel.pack(side="top",expand = False)

        self.chatBox = ctk.CTkTextbox(self,width=220,height=55)
        self.chatBox.pack(side="top",padx=10,pady=10,fill="both",expand = True)

        self.button = ctk.CTkButton(self,width = 200,height=55,text="Submit")
        self.button.pack(side="bottom",padx=10,pady=10,fill="x")
        



class BottomFrame(ctk.CTkFrame):

    def __init__(self,parent,TextBox,**kwargs):
        super().__init__(parent,**kwargs)
        self.audioQueue = Queue()
        self.Buttons()
        self.TextBox = TextBox
        self.STTEngine = None
        self.SummaryEngine = None
        self.exit_signal = threading.Event()
        self.ENDRECORDING = False
        self.playOn = False
        self.isPause = False
        self.isStop = True
        self.canSum = False
        self.playTime = 0
        self.CurrPauseTime = 0
        self.seconds = None
        self.Millisec = None
        self.Clear = None
        self.default_fg = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        self.default_hover = ctk.ThemeManager.theme["CTkButton"]["hover_color"]
        self.check()

    def Play(self):
            
            if self.playOn:
                return 

            if not self.isStop:
                self.exit_signal.clear()
                self.playTime = self.playTime
                self.isPause = False     
            else:
                self.TextBox.configure(state="normal")
                self.TextBox.delete("0.0","end")
                self.TextBox.configure(state="disabled")
                self.exit_signal.clear()
                self.playTime = time.time()
            
            if self.Clear != None:
                self.Clear.place_forget()

            self.playOn = True
            self.isStop = False
            self.canSum = False
            self.ENDRECORDING = False
            self.STTEngine = threading.Thread(
                        target=TextListener.AudioListener,
                        args=(self.audioQueue,self.exit_signal,),
                        daemon=True)
            self.STTEngine.start()
            self.play.configure(text="Recording...", state="disabled",fg_color = "darkred")
            self.pause.configure(text="Pause", state="normal",fg_color = self.default_fg)

    def Pause(self):
        if not self.isStop:
                self.isPause = True
                self.playOn = False
                self.CurrPauseTime = time.time()
                self.play.configure(text="Play", state="disabled",fg_color = self.default_fg)
                self.PauseAnimation()
                self.exit_signal.set()
        else:
            messagebox.showinfo("NOT Recording","You haven't pressed Play Yet")


    def Stop(self):
        if not self.isStop:
            self.playOn = False
            self.play.configure(text="Play", state="normal",fg_color = self.default_fg)
            self.pause.configure(text="Pause", state="normal",fg_color = self.default_fg)
            self.playTime = 0
            self.Clear = ctk.CTkButton(self.TextBox,text="Clear",width=75,height=25,fg_color="transparent",
                                       hover_color="black",command=self.clear)
            self.StopAnimation()
            if self.isPause: 
                self.stop.configure(text="Processing Final Audio...",fg_color="darkred",state="disabled")
                self.after(100,self.StopPause)

            self.exit_signal.set()
            self.isStop = True
            
        else:
            messagebox.showinfo("NOT Recording","You haven't pressed Play Yet")

    def clear(self):
        self.TextBox.configure(state="normal")
        self.TextBox.delete("0.0","end")
        self.TextBox.configure(state="disabled")
    
    def StopPause(self):
        
        self.stop.configure(text="Stop",state="normal",fg_color=self.default_fg)
        
        self.isPause = False
        


    def StopAnimation(self):
            if  self.ENDRECORDING :
                self.stop.configure(text="Stop",state="normal",fg_color=self.default_fg)
                self.play.configure(state="normal")
                self.pause.configure(state ="normal")
                self.Clear.place(x=550,y=425)
                self.canSum = True
                return 

            self.stop.configure(text="Processing Final Audio...", state="disabled",fg_color="darkred")
            self.play.configure(state="disabled")
            self.pause.configure(state ="disabled")

            self.after(10,self.StopAnimation)

    def PauseAnimation(self):

        if  self.ENDRECORDING :
                self.pause.configure(text="Play To Unpause...",state="disabled",fg_color="darkred")
                self.play.configure(state="normal")   
                self.stop.configure(state="normal")
                return

        self.pause.configure(text="Pausing Recording", state="disabled")
        self.pause.configure(fg_color="darkred")

        self.stop.configure(state="disabled")

        self.after(10,self.PauseAnimation)

    

        
        

    def check(self):
        try:
           while True:
               text = self.audioQueue.get_nowait()
               self.audioQueue.task_done()
               if text == 1:
                   self.ENDRECORDING = True
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

class RecFrame(ctk.CTkFrame):
    def __init__(self,parent,bottomBar,**kwargs):
        super().__init__(parent,**kwargs)
        self.bottomBar = bottomBar
        self.TextBoxQueueIn = Queue()
        self.TextBoxQueueOut = Queue()
        self.BreakCheck = False
        self.TotalPauseTime = 0
        self.CurrPauseTime = 0
        self.Minutes = 0
        self.Sec = None
        self.Mil = None
        self.inFrame()
    
    def inFrame(self):
        self.grid_propagate(False)
        self.pack_propagate(False)

        
        self.fileName = ctk.CTkEntry(self,width=200)
        self.save = ctk.CTkButton(self,width=200,text="Save",state="disabled")


        self.recTimer = ctk.CTkLabel(self,width=150,height=70,text="00:00.00",fg_color="black",bg_color="transparent",corner_radius=50)

        self.sumbum = ctk.CTkButton(self,width=200,text="Summarize",command=self.SummRizer,state="disabled")
        self.stateChange = False


        self.grid_columnconfigure(0,weight=0)
        self.grid_columnconfigure(1,weight=1)
        self.grid_columnconfigure(2,weight=1)
        self.grid_columnconfigure(3,weight=1)
        self.grid_rowconfigure(1,weight=1)

        
        self.recTimer.grid(row=1,column=0,padx=20,pady=20,sticky="ns")
        self.fileName.grid(row=1,column=1,padx=20,pady=20,sticky="ns")
        self.save.grid(row=1,column=2,padx=20,pady=20,sticky="ns")
        self.sumbum.grid(row=1,column=3,padx=20,pady=20,sticky="ns")
        self.PlayRec()
        self.SumStart()
    
    def PlayRec(self):
        if self.bottomBar.playOn:
        
                elapsed = time.time() - self.bottomBar.playTime - self.TotalPauseTime
                self.val = max(0, int(elapsed * 10))
               
                self.Sec = (self.val // 10) % 60
                self.Mil = self.val % 10
                self.Minutes = self.val // 600
        
                self.recTimer.configure(text=f"{self.Minutes:02d}:{self.Sec:02d}.{self.Mil}",fg_color="red")
        else:
            if self.bottomBar.isPause:
                now = time.time()

                self.TotalPauseTime += now - self.bottomBar.CurrPauseTime
                self.bottomBar.CurrPauseTime = now
                self.TotalPauseTime  += time.time() - self.bottomBar.CurrPauseTime
                self.recTimer.configure(text=f"{self.Minutes:02d}:{self.Sec:02d}.{self.Mil}",fg_color="black")
                
            elif self.bottomBar.isStop:
                self.TotalPauseTime = 0
                self.bottomBar.CurrPauseTime = 0
                self.Sec = 0
                self.Mil = 0
                self.Minutes = 0
                self.recTimer.configure(text="00:00.00",fg_color="black")

        self.after(100,self.PlayRec)

    def SumStart(self):
        if self.bottomBar.canSum and self.bottomBar.ENDRECORDING and not self.stateChange:
            self.sumbum.configure(state="normal")
            self.save.configure(state="normal")
            self.stateChange = True
        elif not self.bottomBar.canSum:
            self.sumbum.configure(state="disabled")
            self.save.configure(state="disabled")
            self.stateChange = False
        self.after(100,self.SumStart)
    
    def SummRizer(self):
        if self.bottomBar.exit_signal.is_set():
            
            self.Sequecncing = threading.Thread(
                target = self.sequencer,
                daemon=True
            )
            self.Sequecncing.start()
        else:
            print("YOU HAVE TO STOP BRUH")


    def sequencer(self):
        print("HoLi")
        if self.bottomBar.STTEngine.is_alive():
            self.bottomBar.STTEngine.join()
    

        self.BreakCheck = False
        if self.bottomBar.ENDRECORDING:
            print("Starting")

            self.TextBoxQueueIn.put(self.bottomBar.TextBox.get("1.0","end-1c"))
            self.SummaryEngine = threading.Thread(
                target = TextListener.LLMSummerizer,
                args=(self.TextBoxQueueIn,self.TextBoxQueueOut,),
                daemon=True
            )
            self.SummaryEngine.start()
            self.check()

    def check(self):
        try:
            while True:
                SummaryText = self.TextBoxQueueOut.get_nowait()
                self.bottomBar.TextBox.configure(state="normal")
                self.bottomBar.TextBox.delete("0.0","end")
                self.bottomBar.TextBox.insert("end-1c",SummaryText)
                self.bottomBar.TextBox.configure(state="disabled")
                self.BreakCheck = True

        except queue.Empty:
            pass

        finally:

            if not self.BreakCheck:
                self.after(10,self.check)


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
        self.textBox.pack(side="top",padx=10,pady=10,fill="both",expand=True)
        self.textBox.configure(state="disabled")


        self.bottomFrame= BottomFrame(self,self.textBox,width=700,height=115)
        self.bottomFrame.pack(side="bottom",padx=10,pady=10)

        self.recordBar = RecFrame(self,self.bottomFrame,width=700,height=85)
        self.recordBar.pack(side="top",padx=10,pady=10,fill="both",expand=True)

app = App()
app.maxsize(1201,701)
app.mainloop()