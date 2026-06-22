import speech_recognition as sr
import language_tool_python as lt
import time
import threading
from queue import Queue
import ollama as LLM
import whisper 
from pathlib import Path


LLMthread = None
mainText = ""
FinalTextOutput = ""
audioInput = sr.Recognizer()
tool = lt.LanguageTool("en-GB")
InputQueue = Queue()
stopEvent = threading.Event()
nameText=""
val = False
isTextSave = str(input("Are you saving this text ?(Y/N): "))
if isTextSave.lower() == "y":
      val = True
      nameText = str(input("Whats the name of saveFile: "))


def FinalText(text):
    
    prompt =f"""
        You are the processing engine of an AI Lecture Recorder. Your task is to take a raw, unedited speech-to-text (STT) transcript of a live university lecture, clean up the audio-related noise, and format it into a highly professional, structured study document in Markdown.

        ### INPUT CHARACTERISTICS:
        The input text is from a live recording. It contains filler words ("um", "ah", "like"), professor stumbles, mid-sentence corrections, and phonetic corruptions of technical terms (e.g., mishearing code characters, math symbols, or software commands).

        ### PROCESSING INSTRUCTIONS:
        1. **Filter Audio Noise:** Remove all verbal filler, false starts, and casual conversational tangents that do not contribute to the academic material.
        2. **Technical Translation:** Actively look for phonetically mangled technical terms, equations, or syntax and fix them based on the course context (e.g., if it sounds like code, format it as proper code syntax; if it sounds like a command-line tool, translate it to its valid UNIX/Bash form).
        3. **Extract Actionable Items:** If the professor begins discussing an assignment, exam, deadline, or homework specification mid-lecture, isolate that information and format it clearly.
        4. **Maintain Original Intent:** Fix the grammar, punctuation, and clarity, but never alter the actual instructions, numbers, dates, or logical requirements stated by the instructor.

        ### OUTPUT STRUCTURE REQUIREMENTS:
        Organize the cleaned lecture content into a logical, highly scannable Markdown layout using:
        - **`# Title` and `## Headings`** for distinct topics or lecture segments.
        - **`**Bold text**`** to highlight core definitions, crucial deadlines, or key terms.
        - **Numbered/Bullet Lists** for step-by-step processes or requirement lists.
        - **Code Blocks (` ``` `)** for any terminal commands, scripts, file paths, or directory hierarchies.

        ---

        ### RAW LECTURE RECORDER TRANSCRIPT:
        [{text}]
    """

    response = LLM.generate(
          model="qwen2.5-coder:7b",
          prompt=prompt
          
    )

    FinalText = response['response']


    return FinalText






def LLMStart():
    while True:
                text = InputQueue.get()
                if text is None:
                      InputQueue.task_done()
                      break
                
                ReadContext(text)
                InputQueue.task_done()
    return

def ReadContext(text):
        global mainText
        if text.strip():
            prompt = f"""You are a transcription correction assistant. You will receive raw speech-to-text output that may contain errors.

            Your tasks:
            - Fix misheared or misspelled words based on context
            - Add proper punctuation and capitalization
            - Remove filler words (um, uh, like) unless they seem intentional
            - Keep the original meaning and wording as close as possible
            - Do NOT add new information or rephrase sentences 
            - Convert spoken symbols to ASCII characters:
                - "slash" → /
                - "backslash" → \\
                - "at" or "at sign" → @
                - "dot" or "period" → .
                - "hyphen" or "dash" → -
                - "underscore" → _
                - "hash" or "hashtag" → #
                - "equals" → =
                - "plus" → +
                - "asterisk" or "star" → *

            Raw transcript:
            {text}

            Return only the corrected transcript with no explanation or preamble."""
            response = LLM.generate (
                model="llama3.2:latest",
                prompt=prompt
            )

            mainText+=response["response"]+"\n"


 
LLMthread = threading.Thread(
        target=LLMStart,
        daemon=True
        )
LLMthread.start()


print("Start Talking...")


with sr.Microphone() as source:
            audioInput.adjust_for_ambient_noise(source=source,duration=0.2)
            
            while True:
                try:
                        audio = audioInput.listen(source=source,phrase_time_limit=15)
                        text = audioInput.recognize_whisper(audio, model="base")
                        text = text.lower()
                        InputQueue.put(text)

                except sr.RequestError as e:
                    pass

                except sr.UnknownValueError:
                    pass

                except KeyboardInterrupt:
                    print("\nStopping the Program")
                    InputQueue.put(None)

                    time.sleep(1.0)

                    if mainText:
                        print("\nSaving File")
                        OuterDir = Path("RecordingText")
                        filePath = OuterDir/(nameText+".txt")

                        with open(filePath,'w',encoding="utf-8") as file:
                            file.write(mainText)

                        print("Generating output Summary!!")
                        FinalTextOutput = FinalText(mainText)

                        OuterDir = Path("SummaryText")
                    
                        filePath = OuterDir/(nameText+"--summary.txt")

                        with open(filePath,'w',encoding="utf-8") as file:
                            file.write(FinalTextOutput)

                        print("\nExit")


                    break
























        
