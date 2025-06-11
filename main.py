import os
import re
import subprocess
import threading

import numpy as np
import pvporcupine
import sounddevice as sd
from dotenv import load_dotenv
from google.cloud import texttospeech
from openai import OpenAI

from transcribe import listen_transcribe_respond


def card_number(hint: str, capture=True) -> int:
    """Return ALSA card # that matches `hint` (e.g. 'voicehat' or 'USB')."""
    cmd = ['arecord', '-l'] if capture else ['aplay', '-l']
    out = subprocess.check_output(cmd, text=True)
    for line in out.splitlines():
        if line.startswith('card') and hint.lower() in line.lower():
            return int(re.search(r'card (\d+):', line).group(1))
    raise RuntimeError(f"No ALSA card containing “{hint}” found")


# ─── Environment & Clients ─────────────────────────────────────────────────────
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "keys/voice-command-460016-646f1e7cb362.json"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GPT_API_KEY       = os.getenv("GPT_API_KEY")
PICOVOICE_KEY    = os.getenv("PICOVOICE_KEY")

deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
gpt_client      = OpenAI(api_key=GPT_API_KEY)
gcp_client      = texttospeech.TextToSpeechClient()

voice = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-standard-D",
    ssml_gender=texttospeech.SsmlVoiceGender.MALE
)
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    sample_rate_hertz=48000
)

# ─── Audio Setup ────────────────────────────────────────────────────────────────
MIC     = "sndrpigooglevoi"
SPEAKER = "USB"
in_index  = card_number(MIC, True)
out_index = card_number(SPEAKER, False)
print(f"Mic ALSA card: {in_index}, Speaker ALSA card: {out_index}")

porcupine = pvporcupine.create(
    access_key    = PICOVOICE_KEY,
    keyword_paths = ["Hey_nova/Hey-Nova_en_raspberry-pi_v3_0_0.ppn"]
)

# down‐sample factor if your card is 48 kHz but Porcupine wants 16 kHz
DOWNSAMPLE = 3
block_size  = porcupine.frame_length * DOWNSAMPLE


# ─── Callback ─────────────────────────────────────────────────────────────────
wake_event = threading.Event()
def audio_callback(indata, frames, time, status):
    if status.input_overflow:
        print("⚠️ Audio overflow")
        return
    raw = np.frombuffer(indata, dtype=np.int16)
    # down‐sample 48 k → 16 k
    samples_16k = raw.reshape(-1, DOWNSAMPLE).mean(axis=1).astype(np.int16)

    if porcupine.process(samples_16k) >= 0:
        print("✅ Wake word detected!")
        wake_event.set()          # <- signal main thread
        raise sd.CallbackStop()


# ─── Main loop ─────────────────────────────────────────────────────────────────
try:
    while True:
        wake_event.clear()

        with sd.RawInputStream(
                samplerate=48000,
                blocksize=block_size,
                device=in_index,
                channels=1,
                dtype="int16",
                callback=audio_callback
            ) as stream:

            print("Listening for wake word…  (Ctrl-C to exit)")
            # Block here until wake_event.set() in callback
            wake_event.wait()

        # callback has stopped the stream
        print("Recording speech…")
        listen_transcribe_respond(
            gpt_client,
            deepseek_client,
            gcp_client,
            in_index,
            out_index,
            voice,
            audio_config
        )

        print("\nRestarting wake-word listener...\n")

except KeyboardInterrupt:
    print("\nInterrupted by user. Shutting down.")
finally:
    porcupine.delete()
