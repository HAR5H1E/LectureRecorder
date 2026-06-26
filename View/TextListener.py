import speech_recognition as sr
import ollama as LLM
import queue
from queue import Queue
import threading
import whisper

smoothAudio = Queue()

def startLLM(stopEvent,audioQueue,isPause):
    try: 
        while not stopEvent.is_set():
            text = smoothAudio.get()
            smoothText = ReadContext(text)
            if smoothText is not None:
                    audioQueue.put(smoothText)
                    audioQueue.task_done()
            if isPause.is_set():
                    audioQueue.put(True)
                    audioQueue.task_done()
            else:
                audioQueue.put(False)
                audioQueue.task_done() 

    except queue.Empty:
        return
    
    
def ReadContext(Text):

    print("Wow A text: "+Text)
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


                    Raw transcript:
                    {Text}

                    Return only the corrected transcript, no explanation."""

        response = LLM.generate(
            model="gemma2:9b",
            prompt=prompt
        )

        return response['response']
    return None

def AudioListener(audioQueue,exitSignal,isPause):

    stopEvent = threading.Event()
    Audio = sr.Recognizer()
    LLMThread = threading.Thread(
        target=startLLM,
        args=(stopEvent,audioQueue,isPause),
        daemon=True
    )
    LLMThread.start()
    

    while not exitSignal.is_set():
        with sr.Microphone() as source:
            try:    
                if not isPause.is_set():
                    Audio.adjust_for_ambient_noise(source=source,duration=0.4)
                    Voice = Audio.listen(source=source,phrase_time_limit=30)
                    AudioText = Audio.recognize_whisper(Voice,model="base")
                    smoothAudio.put(AudioText)


            except sr.RequestError:
                pass
            except sr.UnknownValueError:
                pass

    
    stopEvent.set()



