import os
import speech_recognition as sr
import language_tool_python as lt
import time
import threading
from queue import Queue
import ollama as LLM
import whisper 
from pathlib import Path
from datetime import datetime
from google import genai
from dotenv import load_dotenv


LLMthread = None
mainText = ""
FinalTextOutput = ""
audioInput = sr.Recognizer()
tool = lt.LanguageTool("en-GB")
InputQueue = Queue()
nameText=""
val = False


def FinalText(text):
    
    prompt =f"""You are a Markdown document formatter for university lecture notes.

        ## STEP 1 - INFER CONTEXT:
        Before formatting, read the entire transcript and identify:
        - What subject/field is this lecture about?
        - What are the key topics covered?
        - Are there assignments, deadlines, or grading breakdowns?
        - Are there any [UNCLEAR] or [CORRECTED] flags from the previous pass?
        - If there are any words that seem to not be inline with the context of the previous part of the test or later part remove it 
        Use this to decide the document structure before writing anything.

        ## STEP 2 - FORMAT:
        Transform the corrected transcript into structured Markdown.
        - # for main title
        - ## for major sections  
        - ### for subsections
        - **bold** for deadlines, key terms, percentages
        - Regular bullet lists only
        - Code blocks ONLY for actual code or commands

        ## STEP 3 - VALIDATE:
        Before outputting, check:
        - Do all percentage breakdowns add up to 100%? 
        If not add **[VERIFY - incomplete breakdown]**
        - Are all [UNCLEAR] flags preserved and not guessed?
        - Are all dates and deadlines present?
        - Did you add any content not in the input? 
        If yes remove it

        ## STRICT RULES:
        - Do NOT correct errors — mistral already did that
        - Do NOT add closing remarks or encouragement
        - Do NOT wrap bullet lists in code blocks
        - Do NOT hallucinate content
        - Preserve all [UNCLEAR] and [CORRECTED] flags exactly as they appear

        ## INPUT:
        {text}

        ---

       

        Return only the corrected transcript, no explanation.
        """

    load_dotenv()

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    try:
        interaction = client.interactions.create(
            model = "gemini-3.1-flash-lite",
            input = prompt,
            store=False
        )
    except Exception as e:
          
          print("overloaded switiching model...Effictevness might be Reduced")
          interaction = client.interactions.create(
            model = "gemini-2.5-flash",
            input = prompt,
            store = False
        )


    FinalText = interaction.output_text

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
            prompt = f"""You are a transcription correction assistant for university lectures.

                ## STRICT OUTPUT RULES:
                - Output the corrected transcript as clean, continuous prose.
                - Do NOT wrap sentences, phrases, or words in quotation marks (" ").
                - Do NOT include conversational fragments, meta-commentary, or code blocks.
                - Return ONLY the raw, smoothed text.

                ## STEP 1 - INFER CONTEXT:
                Before correcting, read the transcript and identify:
                - What subject/field is this lecture about?
                - What technical terms are likely being used?
                - What type of document is being described?
                Use this inferred context to guide your corrections.

                ## STEP 2 - CORRECT:
                - Fix misheared words based on the inferred context
                - Add proper punctuation and capitalization
                - Remove filler words (um, uh, like)
                - Convert spoken symbols to ASCII:
                    - "slash" → /
                    - "backslash" → \\
                    - "at sign" → @
                    - "dot" → .
                    - "underscore" → _
                    - "hash" → #

                ## STEP 3 - FLAG:
                - Any year that seems anachronistic → correct based on context
                - Any percentage breakdown → verify it totals 100%
                - Anything genuinely unclear → mark as [UNCLEAR]
                - Any correction you're unsure about → mark as [CORRECTED: original]
                so the user can verify


                Raw transcript:
                {text}

                Return only the corrected transcript, no explanation."""
            response = LLM.generate (
                model="gemma2:9b",
                prompt=prompt
            )

            mainText+=response["response"]+"\n"





def audioListener():
        print("Start Talking...")
        with sr.Microphone() as source:
                    audioInput.adjust_for_ambient_noise(source=source,duration=0.2)
                    
                    while True:
                        try:
                                
                                audio = audioInput.listen(source=source,phrase_time_limit=30)
                                text = audioInput.recognize_whisper(audio, model="base")
                                text = text.lower()
                                InputQueue.put(text)

                        except sr.RequestError as e:
                            pass

                        except sr.UnknownValueError:
                            pass

                        except KeyboardInterrupt:
                            return

        

def main():
                
            global nameText
            
            nameText = str(input("Whats the name of saveFile: "))

            
            LLMthread = threading.Thread(
                target=LLMStart,
                daemon=True
            )
            LLMthread.start()
            
            
            audioListener()

            
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
                            
                filePath = OuterDir/(nameText+"--summarized.txt")

                with open(filePath,'w',encoding="utf-8") as file:
                    file.write(FinalTextOutput)

                print("\nExit")

main() 