import os
import speech_recognition as sr
import ollama as LLM
import queue
import threading
import whisper
from queue import Queue
from google import genai
from pathlib import Path
from dotenv import load_dotenv


smoothAudio = Queue()
PauseThread = threading.Event()
History = []
count = 1
def startLLM(stopEvent,audioQueue):
    global History,count
    while not stopEvent.is_set():
        text = smoothAudio.get()
        smoothAudio.task_done()
        if text == 1:
             break
        smoothText = ReadContext(text)
        if smoothText is not None:
            audioQueue.put(smoothText)
            History.append({f"AudioChunk " : count, "TextRecording":smoothText})
            count+=1
    audioQueue.put(1)
    History = []
def ReadContext(Text):
    global History
    CurrHis = []
    if History == []:
         CurrHis = [{f"AudioChunk " : 0, "TextRecording":""}]
    else:
        if len(History) >= 3:
            CurrHis = History[-3:]
        else:
            CurrHis = History
    print(CurrHis)
    if Text.strip():
        prompt=f"""You are a transcription correction assistant for university lectures.

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

                    ## Step 4 - History
                    - Use The History context from the last Few Recordings to 
                    help better smooth out the current text

                    History:
                    {CurrHis}

                    Raw transcript:
                    {Text}

                    Return only the corrected transcript, no explanation."""

        response = LLM.generate(
            model="gemma2:9b",
            prompt=prompt
        )

        return response['response']
    return None

def AudioListener(audioQueue,exitSignal):
    global count
    stopEvent = threading.Event()
    Audio = sr.Recognizer()
    LLMThread = threading.Thread(
        target=startLLM,
        args=(stopEvent,audioQueue,),
        daemon=True
    )
    LLMThread.start()
    
    with sr.Microphone() as source:
        Audio.adjust_for_ambient_noise(source=source,duration=0.4)
        while not exitSignal.is_set():
                try:    
                        
                        Voice = Audio.listen(source=source,phrase_time_limit=15)
                        if not exitSignal.is_set():  
                            AudioText = Audio.recognize_whisper(Voice,model="base")
                            smoothAudio.put(AudioText)  
                        else:
                            smoothAudio.put(1)
                            stopEvent.set()



                except sr.RequestError:
                    pass
                except sr.UnknownValueError:
                    pass
                except sr.WaitTimeoutError:
                     pass


    smoothAudio.put(1)
    count = 0
    
    stopEvent.set()
    print("I am Stopin?")


def LLMSummerizer(TextBoxQueueIn,TextBoxQueueout):
        FinalText = TextBoxQueueIn.get()
        if FinalText.strip():
            ParentDir = Path(__file__).resolve().parent
            scriptDir = ParentDir.parent
            envDir = scriptDir/ ".env"
            load_dotenv(envDir)
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

            prompt = f"""You are a Markdown document formatter for university lecture notes.

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
            {FinalText}

            ---

        

            Return only the corrected transcript, no explanation.
            """
            print("Ok Starting")
            try:
                
                response = client.interactions.create(
                    model = "gemini-3.1-flash-lite",
                    input = prompt,
                    store=False,
                    generation_config={
                        "temperature":0
                    }
                )
            except Exception as e:
                response = client.interactions.create(
                    model = "gemini-2.5-flash",
                    input = prompt,
                    store=False,
                    generation_config={
                        "temperature":0
                    }
                )

            print("Sending Response")
            TextBoxQueueout.put(response.output_text)

        return 

