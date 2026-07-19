import customtkinter as ctk
import threading
import os
import TextListener
import RagLLm
import queue
from queue import Queue
from tkinter import messagebox
from pathlib import Path
import time
import pymupdf

TextBoxValue = None
saveButton = None
sumButton = None
comrecVar = None
RecComboBox = None
CurrFile = None

ParentDir = Path(__file__).resolve().parent
scriptDir = ParentDir.parent
RecText = scriptDir/ "SummaryText"

class TabView(ctk.CTkTabview):
    def __init__(self, master ,ChoiceMenu, **kwargs):
        super().__init__(master, **kwargs)
        self.add("RecView")
        self.add("SaveView")
        self.RecBox = None
        self.SaveBox = None
        self.ChoiceMenu = ChoiceMenu
        self.GetVal = Queue()
        self.repeatisTab=False
        self.repeatisNTab = False
        self.stopSave = False
        self.Tabs()
        self.checkTab()
    
    def Tabs(self):

        self.RecBox = ctk.CTkTextbox(self.tab("RecView"),width=700,height=400)
        self.RecBox.pack(side="top",fill="both",expand=True)
        self.RecBox.configure(state="disabled")

        self.SaveBox =  ctk.CTkTextbox(self.tab("SaveView"),width=700,height=400)
        self.SaveBox.pack(side="top",fill="both",expand=True)
        self.SaveBox.configure(state="disabled")

        self.Clear = ctk.CTkButton(self.SaveBox,text="Clear",width=75,height=25,fg_color="transparent",
                                       hover_color="black",command=self.clear)
        
        self.Edit = ctk.CTkButton(self.SaveBox,text="Edit",width=75,height=25,fg_color="transparent",
                                       hover_color="black",command=self.edit)
        
        self.Save = ctk.CTkButton(self.SaveBox,text="Save",width=75,height=25,fg_color="transparent",
                                       hover_color="black",command=self.save)
        self.Delete = ctk.CTkButton(self.SaveBox,text="Delete",width=75,height=25,fg_color="transparent",
                                       hover_color="black",command=self.delete)
        
        self.Edit.place(x=435,y=375)
        self.Clear.place(x=510,y=375)
        self.Save.place(x=585,y=375)
        self.Delete.place(x=660,y=375)
        

    def getRec(self):
        return self.RecBox

    def getSave(self):
        return self.SaveBox
    
    def clear(self):
        self.SaveBox.configure(state="normal")
        self.SaveBox.delete("0.0","end")
        self.SaveBox.configure(state="disabled")
    

    def edit(self):
        if (self.SaveBox.get("1.0","end-1c")):
            self.SaveBox.configure(state="normal")
        else:
            messagebox.showinfo("NOT Text Available","TextBox Empty")

    def save(self):
        global CurrFile
        self.stopSave = False
        if self.SaveBox.get("0.0","end").strip():
            with open(CurrFile,"w") as file:
                file.write(self.SaveBox.get("0.0","end"))
            
            sequencerThread = threading.Thread(
                target=self.saveSequencer,
                daemon = True
            )
            sequencerThread.start()
            self.saveAnimation()
            
        else:
            self.delete()
    def saveSequencer(self):
        global CurrFile 
        DelThread = threading.Thread(
            target=RagLLm.deleteQuery,
            args=(str(CurrFile),),
            daemon=True
        )
        DelThread.start()
        time.sleep(0.5)
        if DelThread.is_alive():
            DelThread.join()
        
        textLength = len(self.SaveBox.get("0.0","end"))
        maxChar = 300
        chunkSize = 150
        overLap = 20
        if (textLength * 1.77 > 5000):
                maxChar = 2000
                chunkSize = 256
                overLap = 50
        elif (textLength * 1.77 < 5000 and  textLength * 1.77 > 1000 ):
                maxChar = 1000
                chunkSize = 200
                overLap = 40
        else:
                maxChar = 500
                chunkSize = 180
                overLap = 36


        SaveThread = threading.Thread(
            target=RagLLm.EncodeContextText,
            args=(self.SaveBox.get("0.0","end"),
                        maxChar,
                        chunkSize,
                        overLap,
                        self.GetVal,
                        str(CurrFile),)
        )
        SaveThread.start()

    def saveAnimation(self):
        try:
            while True:
                RecVal = self.GetVal.get_nowait()
                if RecVal == True:
                    messagebox.showinfo("Save", "File Saved")
                    self.stopSave = True
                    break
        except queue.Empty:
            pass
        finally:

            if not self.stopSave:
                self.after(10,self.saveAnimation)

    def delete(self):
        global CurrFile
        print(CurrFile)
        DelThread = threading.Thread(
            target=RagLLm.deleteQuery,
            args=(str(CurrFile),),
            daemon=True
        )
        DelThread.start()
        os.remove(CurrFile)
        CurrFile = None
        RecComboBox.configure(values = ["-"]+os.listdir(RecText))
        comrecVar.set("SummaryNotes")
        self.SaveBox.configure(state="normal")
        self.SaveBox.delete("0.0","end")
        self.SaveBox.configure(state="disabled")


    def checkTab(self):
        if self.ChoiceMenu.select:
            if self.get() != "SaveView":
                    self._segmented_button._buttons_dict["SaveView"].configure(text_color="yellow")
            else:
                    self.ChoiceMenu.select = False
        else:
            self._segmented_button._buttons_dict["SaveView"].configure(text_color="white")    

        self.after(350,self.checkTab)

class innerLeftFrame(ctk.CTkFrame):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,**kwargs)
        global TextBoxValue,comrecVar,RecText,RecComboBox
        self.grid_propagate(False)
        self.grid_rowconfigure(0,weight=0)
        self.grid_rowconfigure(1,weight=0)
        self.grid_rowconfigure(2,weight=0)
        self.grid_rowconfigure(3,weight=0)
        
        comrecVar=self.ComboRecVar = ctk.StringVar(value="SummaryNotes")
        self.Combolist = ["-"]
        self.textBox = TextBoxValue
        self.Rectext=""
        RecComboBox=self.RecBox = ctk.CTkOptionMenu(self,
                                                    width=180,
                                                    values=["-"]+os.listdir(RecText),
                                                    variable=self.ComboRecVar,
                                                    command = self.selectOption)
        self.RecBox.grid(row=0,column=0,padx=20,pady=20,sticky="ne")

        self.HighlightText = ctk.CTkLabel(self,text="HighlightText",width=180)
        self.HighlightText.grid(row=1,column=0,sticky="nsew")

        self.Highlight = ctk.CTkTextbox(self,
                                        width=180,state="normal")
        self.Highlight.grid(row=2,column=0,padx=20,pady=20,sticky="nsew")

        self.SavePdfButton = ctk.CTkButton(self,text="SAVE AS PDF",command=self.savePDF,state="disabled")
        self.SavePdfButton.grid(row=3,column=0,padx=20,pady=20,sticky="nsew")
        self.select = False
    
    def savePDF(self):
        global CurrFile
        
        md_doc = pymupdf.open(CurrFile)
        DeskPath = Path.home() / "Desktop"
        newFolder = DeskPath / "PDFLECREC"
        newFolder.mkdir(parents=True, exist_ok=True)

        original_name = Path(CurrFile).stem
        output_path = newFolder / f"{original_name}.pdf"
        md_doc.ez_save(output_path)
    
    def getText(self):
        return self.Highlight

    def selectOption(self,choice):
        global CurrFile
        if choice == "-":
            self.ComboRecVar.set("SummaryNotes")
            TextBoxValue.configure(state="normal")
            TextBoxValue.delete("0.0","end")
            TextBoxValue.configure(state="disabled")
            self.SavePdfButton.configure(state="disabled")
            CurrFile = None
        else:

            TextBoxValue.configure(state="normal")
            TextBoxValue.delete("0.0","end")
            CurrFile = option = RecText/choice
            with open(option,'r') as file:
                TEXT=file.read()
                TextBoxValue.configure(state="normal")
                TextBoxValue.insert("0.0",TEXT)
                TextBoxValue.configure(state="disabled")
            self.SavePdfButton.configure(state="normal")
            self.select = True

            

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

        self.innerFrame = innerLeftFrame(self,width=225)
        self.innerFrame.grid(row = 1,column = 0,padx = 20, pady=20,sticky="ns")
    

class RightFrame(ctk.CTkFrame):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,**kwargs)

        self.grid_propagate(False)
        self.pack_propagate(False)
        self.stopAnimation = False
        self.textBox = ctk.CTkTextbox(self,width=240,height=500,state="disabled",font=ctk.CTkFont(size=12))
        self.textBox.pack(side="top",pady=10,expand = False)

        self.QueLabel = ctk.CTkLabel(self,width=220,height=5,text="Ask a Question")
        self.QueLabel.pack(side="top",expand = False)

        self.chatBox = ctk.CTkTextbox(self,width=220,height=55)
        self.chatBox.pack(side="top",padx=10,pady=10,fill="both",expand = True)

        self.button = ctk.CTkButton(self,width = 200,height=55,text="Submit",command=self.submit)
        self.button.pack(side="bottom",padx=10,pady=10,fill="x")
        self.resVal = Queue()
    
    def submit(self):
        if (self.chatBox.get("0.0","end").strip() and CurrFile):

            self.SubmitThread = threading.Thread(
                    target=RagLLm.encodeQuery,
                    args= (self.chatBox.get("0.0","end"),
                        str(CurrFile),
                        self.resVal),
                        daemon = True
                )

            self.SubmitThread.start()
            self.button.configure(text="Processing..",state="disabled")
            self.stopAnimation = False
            self.submitAnimation()
        else:

            messagebox.showinfo("Empty submit Box or No file chosen", "Submit Box is Empty or file not selcted")
    
    def submitAnimation(self):
        try:
            while True:
                RecVal = self.resVal.get_nowait()
                if RecVal == True:
                    self.button.configure(text="Submit",state="normal")
                    self.chatBox.delete("0.0","end")
                    self.SubmitThread.join()
                    self.stopAnimation = True
                    return
                elif RecVal == False:
                    self.button.configure(text="Submit",state="normal")
                    self.textBox.insert("end-1c",("-"*34)+"\n")
                    self.textBox.insert("end-1c","[ERROR]: "+"Application Failed Please Restart App"+"\n\n")
                    self.textBox.insert("end-1c","\n"+("-"*34)+"\n")
                    self.chatBox.delete("0.0","end")
                    self.SubmitThread.join()
                    self.stopAnimation = True
                    return
                else: 
                    self.textBox.configure(state="normal")
                    self.textBox.insert("end-1c",("-"*34)+"\n")
                    self.textBox.insert("end-1c","[QUESTION]: "+self.chatBox.get("0.0","end")+"\n\n")
                    self.textBox.insert("end-1c","[ANSWER]: "+RecVal)
                    self.textBox.insert("end-1c","\n"+("-"*34)+"\n")
                    self.textBox.see("end")
                    self.textBox.configure(state="disabled")
        except queue.Empty:
            pass
        finally:
            if not self.stopAnimation :
                self.after(10,self.submitAnimation)
        

class BottomFrame(ctk.CTkFrame):

    def __init__(self,parent,TextBox,**kwargs):
        super().__init__(parent,**kwargs)
        global HasStopped,RecComboBox
        self.audioQueue = Queue()
        self.TextBox = TextBox
        self.STTEngine = None
        self.SummaryEngine = None
        self.exit_signal = threading.Event()
        self.ENDRECORDING = True
        self.playOn = False
        self.isPause = False
        self.isStop = True
        self.stopAni = False
        self.PauseAni = False
        self.canSum = False
        self.playTime = 0
        self.CurrPauseTime = 0
        self.seconds = None
        self.Millisec = None
        self.Clear = None
        self.Edit = None
        HasStopped = self.isStop
        self.default_fg = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        self.default_hover = ctk.ThemeManager.theme["CTkButton"]["hover_color"]
        self.Buttons()
        self.check()
        self.editClearButtons()

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
            self.stopAni = False
            self.pauseAni = False
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
            self.StopAnimation()
            if self.isPause: 
                self.stop.configure(text="Processing Final Audio...",fg_color="darkred",state="disabled")
                self.after(100,self.StopPause)

            self.exit_signal.set()
            self.isStop = True
            
        else:
            messagebox.showinfo("NOT Recording","You haven't pressed Play Yet")

    def clear(self):
        global sumButton,saveButton
        if not self.isPause:
            self.TextBox.configure(state="normal")
            self.TextBox.delete("0.0","end")
            self.TextBox.configure(state="disabled")
            comrecVar.set("SummaryNotes")
    
    def edit(self):
        self.TextBox.configure(state="normal")
      
    
    def StopPause(self):
        
        self.stop.configure(text="Stop",state="normal",fg_color=self.default_fg)
        self.isPause = False
        
    def editClearButtons(self):
        if self.ENDRECORDING:
            self.Edit.place(x=560,y=375)
            if not self.isPause:
                self.Clear.place(x=635,y=375)
        else:
            self.Edit.place_forget()
            self.Clear.place_forget()

        self.after(10,self.editClearButtons)
        


    def StopAnimation(self):
            if  self.ENDRECORDING :
                self.stop.configure(text="Stop",state="normal",fg_color=self.default_fg)
                self.play.configure(state="normal")
                self.pause.configure(state ="normal")
                self.Edit.place(x=560,y=375)
                self.Clear.place(x=635,y=375)
                self.canSum = True
                self.stopAni = True
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
               print(text)
               self.audioQueue.task_done()
               if text == 1:
                   self.ENDRECORDING = True
                   while not self.audioQueue.empty():
                        try:
                            self.audioQueue.get_nowait()
                            self.audioQueue.task_done() 
                            print("EMPTYING AUDIO") 
                        except queue.Empty:
                            break
                   return
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

        self.Clear = ctk.CTkButton(self.TextBox,text="Clear",width=75,height=25,fg_color="transparent",
                                       hover_color="black",command=self.clear)
        self.Edit = ctk.CTkButton(self.TextBox,text="Edit",width=75,height=25,fg_color="transparent",
                                       hover_color="black",command=self.edit)

class RecFrame(ctk.CTkFrame):
    def __init__(self,parent,bottomBar,HighText,**kwargs):
        super().__init__(parent,**kwargs)
        self.bottomBar = bottomBar
        self.HighLight = HighText
        self.TextBoxQueueIn = Queue()
        self.TextBoxQueueOut = Queue()
        self.GetVal = Queue()
        self.BreakCheck = False
        self.hasSumStart = False
        self.TotalPauseTime = 0
        self.CurrPauseTime = 0
        self.Minutes = 0
        self.fileName = None
        self.Sec = None
        self.Mil = None
        self.stopSave = False
        self.inFrame()
    
    def inFrame(self):
        global saveButton,sumButton
        self.grid_propagate(False)
        self.pack_propagate(False)

        
        self.fileName = ctk.CTkEntry(self,width=200)
        saveButton = self.save = ctk.CTkButton(self,width=200,text="Save",state="disabled",command=self.Save)


        self.recTimer = ctk.CTkLabel(self,width=150,height=70,text="00:00.00",fg_color="black",bg_color="transparent",corner_radius=50)
     

        sumButton = self.sumbum = ctk.CTkButton(self,width=200,text="Summarize",command=self.SummRizer,state="disabled")
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
    
    def Save(self):
            if self.fileName.get():
                self.stopSave = False
                self.save.configure(text="Saving..",state="disabled")
                with open((RecText/self.fileName.get()).with_suffix(".md"),'w') as file:
                    file.write(self.bottomBar.TextBox.get("1.0","end-1c"))
                
                RecComboBox.configure(values = ["-"]+os.listdir(RecText))
                textLength = len(self.bottomBar.TextBox.get("1.0","end-1c"))
                maxChar = 300
                chunkSize = 150
                overLap = 20
                if (textLength * 1.77 > 5000):
                    maxChar = 2000
                    chunkSize = 256
                    overLap = 50
                elif (textLength * 1.77 < 5000 and  textLength * 1.77 > 1000 ):
                    maxChar = 1000
                    chunkSize = 200
                    overLap = 40
                else:
                    maxChar = 500
                    chunkSize = 180
                    overLap = 36


                SaveThread = threading.Thread(
                    target=RagLLm.EncodeContextText,
                    args=(self.bottomBar.TextBox.get("1.0","end-1c"),
                                                    maxChar,
                                                    chunkSize,
                                                    overLap,
                                                    self.GetVal,
                                                    str(RecText/self.fileName.get())+".md")
                )
                SaveThread.start()
                self.saveAnimation()
        
            else:
                messagebox.showinfo("Didnt name File", "Missing Filename")
    
    def saveAnimation(self):
        try:
            while True:
                RecVal = self.GetVal.get_nowait()
                if RecVal == True:
                    messagebox.showinfo("Save", "File Saved")
                    self.save.configure(text="Save",state="normal")
                    self.fileName.delete(0,"end")
                    self.stopSave = True
                    break
        except queue.Empty:
            pass
        finally:

            if not self.stopSave:
                self.after(10,self.saveAnimation)
            
    def SumStart(self):
        if self.bottomBar.isStop\
                and self.bottomBar.TextBox.get("1.0","end-1c").strip()\
                    and not self.stateChange:
            
            self.sumbum.configure(state="normal")
            self.save.configure(state="normal")
            self.stateChange = True
            
        elif self.bottomBar.isStop\
                and not self.bottomBar.TextBox.get("1.0","end-1c").strip():
            self.sumbum.configure(state="disabled")
            self.save.configure(state="disabled")
            self.stateChange = False
        if  not self.hasSumStart:
            self.after(100,self.SumStart)
    
    def SummRizer(self):
        if self.bottomBar.isStop\
                and self.bottomBar.TextBox.get("1.0","end-1c").strip():
            
            self.Sequecncing = threading.Thread(
                target = self.sequencer,
                daemon=True
            )
            self.Sequecncing.start()
        else:
            print("YOU HAVE TO STOP BRUH")


    def sequencer(self):

        if self.bottomBar.STTEngine != None:
            if self.bottomBar.STTEngine.is_alive():
                self.bottomBar.STTEngine.join()
    

        self.BreakCheck = False
        if self.bottomBar.ENDRECORDING:
            print("Starting")
            if  self.bottomBar.TextBox.get("0.0","end"):
                self.TextBoxQueueIn.put(self.bottomBar.TextBox.get("1.0","end-1c"))
                self.SummaryEngine = threading.Thread(
                    target = TextListener.LLMSummerizer,
                    args=(self.TextBoxQueueIn,
                          self.TextBoxQueueOut,
                          self.HighLight.get("0.0","end"),
                          ),
                    daemon=True
                )
                
                self.SummaryEngine.start()
                self.hasSumStart = True
                self.sumbum.configure(state="disabled")
                self.save.configure(state="disabled")
                self.check()
            else:
                return

    def check(self):
        try:
            while True:
                SummaryText = self.TextBoxQueueOut.get_nowait()
                self.bottomBar.TextBox.configure(state="normal")
                self.bottomBar.TextBox.delete("0.0","end")
                self.bottomBar.TextBox.insert("end-1c",SummaryText)
                self.bottomBar.TextBox.configure(state="disabled")
                self.sumbum.configure(state="normal")
                self.save.configure(state="normal")
                self.BreakCheck = True
                self.hasSumStart = False
                self.SumStart()
                break


        except queue.Empty:
            pass

        finally:

            if not self.BreakCheck:
                self.after(10,self.check)
                


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LECRec")
        self.geometry("1300x700")

        
        self.leftFrame_1 = LeftFrame(self,width=250)
        self.leftFrame_1.pack(side="left",padx=10,pady=10,fill='y',expand=False)

        self.rightFrame_1 = RightFrame(self,width=250)
        self.rightFrame_1.pack(side="right",padx=10,pady=10,fill='y',expand=False)

        self.tabview= TabView(self,self.leftFrame_1.innerFrame,width=700,height=400)
        self.tabview.pack(side="top",fill="x")

        self.textBox = self.tabview.getRec()

        global TextBoxValue
        TextBoxValue = self.tabview.getSave()

        self.bottomFrame= BottomFrame(self,self.textBox,width=700,height=115)
        self.bottomFrame.pack(side="bottom",padx=10,pady=10,fill="x")

        self.recordBar = RecFrame(self,self.bottomFrame,self.leftFrame_1.innerFrame.getText(),width=700,height=85)
        self.recordBar.pack(side="top",padx=10,pady=10,fill="x",expand=True)

        



app = App()
app.maxsize(1301,701)
app.mainloop()