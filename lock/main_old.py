import pvporcupine
import pyaudio
import struct
import os
import scipy.signal
import numpy as np
from dotenv import load_dotenv
from transcribe import listen_transcribe_respond

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "keys/voice-command-460016-646f1e7cb362.json"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GPT_API_KEY= os.getenv("GPT_API_KEY")
PICOVOICE_KEY = os.getenv("PICOVOICE_KEY")
KEYWORD_PATH = "Hey_nova/Hey-Nova_en_raspberry-pi_v3_0_0.ppn"
IN_INDEX = 0
OUT_INDEX = 1
porcupine = pvporcupine.create(access_key = PICOVOICE_KEY, keyword_paths=[KEYWORD_PATH])
pa = pyaudio.PyAudio()
stream = pa.open(
	format				= pyaudio.paInt16,
	channels			= 1,
	rate				= 48000,	# 16 kHz for porcupine but I2S only has 48 KHz
	input				= True,
	input_device_index	= IN_INDEX,
	frames_per_buffer	= porcupine.frame_length
)

print("Listening for wake word…  (Ctrl-C to exit)")
try:
	while True:
		audio_data		= stream.read(porcupine.frame_length, exception_on_overflow=False)
		samples			= struct.unpack_from("h" * porcupine.frame_length, audio_data)
		audio_data = stream.read(1440, exception_on_overflow=False)  # 48000 Hz / 100 fps = 480 samples/frame
		samples_48k = np.frombuffer(audio_data, dtype=np.int16)

		# Resample to 16000 Hz to match Porcupine
		samples_16k = scipy.signal.resample(samples_48k, porcupine.frame_length).astype(np.int16)

		if porcupine.process(samples_16k) >= 0:
			print("Wake word detected!")
			# 🛑 Close PyAudio stream before switching to sounddevice
			stream.stop_stream()
			stream.close()
			listen_transcribe_respond(DEEPSEEK_API_KEY, GPT_API_KEY, IN_INDEX, OUT_INDEX)
			stream = pa.open(
				format				= pyaudio.paInt16,
				channels			= 1,
				rate				= 48000,	# 16 kHz for porcupine but I2S only has 48 KHz
				input				= True,
				input_device_index	= IN_INDEX,
				frames_per_buffer	= porcupine.frame_length
			)
			print("Listening for wake word…")
except KeyboardInterrupt:
	print("\nInterrupted.  Shutting down.")
finally:
	stream.stop_stream();	stream.close()
	pa.terminate();		porcupine.delete()
