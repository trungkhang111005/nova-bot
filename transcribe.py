import serial # For UART
import time # For UART
import sounddevice as sd
import numpy as np
import openai  # or your DeepSeek API wrapper
import io
import time
import tempfile
import soundfile as sf  # add to imports
import queue
import json
from scipy.io import wavfile
from ask_deepseek import get_output
from google.cloud import texttospeech
def rms(chunk):
	return np.sqrt(np.mean(chunk**2))


def speak_with_gcp(deepseek_response, out_index, client, voice, audio_config):
	try:
		synthesis_input = texttospeech.SynthesisInput(text=deepseek_response)

		response = client.synthesize_speech(
			input=synthesis_input,
			voice=voice,
			audio_config=audio_config
		)
		# Play with sounddevice
		wav_data = response.audio_content
		wav_buffer = io.BytesIO(wav_data)

		# Read WAV from memory buffer
		samplerate, audio_array = wavfile.read(wav_buffer)

		# Play
		sd.play(audio_array, samplerate = samplerate ,device=out_index)
		sd.wait()
	except KeyboardInterrupt:
		print("keyboard Interrupt during gcp speaking!")
		sd.stop()

def record_until_silence(in_index: int, sample_rate=48000, threshold=0.0012, silence_duration=1.0, max_duration=15, chunk_duration=0.1):
	try:
		q_buffer = queue.Queue()
		silence_counter = 0
		speaking_started = False
		silence_start_time = None
		loud_chunk_counter = 0
		chunk_samples = int(sample_rate * chunk_duration)
		max_chunks = int(max_duration / chunk_duration)
		def callback(indata, frames, time_info, status):
			if status:
				print("Callback status:", status)
			print(f"{rms(indata)}")
			q_buffer.put(indata.copy())
		print(f"Listening...")
		buffer = []
		with sd.InputStream(samplerate=sample_rate, channels=1, device= in_index, dtype='float32', blocksize=chunk_samples, callback=callback):
			for _ in range(max_chunks):
				chunk = q_buffer.get()
				chunk = np.squeeze(chunk)

				if rms(chunk) >= threshold:
					loud_chunk_counter += 1
				else:
					loud_chunk_counter = 0
				if loud_chunk_counter >= 3:
					speaking_started = True
					silence_start_time = None
				elif speaking_started:
					if silence_start_time == None:
						silence_start_time = time.time()
					elif time.time() - silence_start_time >= silence_duration:
						print("Silence -> Stopping.")
						break
				buffer.append(chunk)
		audio = np.concatenate(buffer)
		if audio.size == 0:
			print("No audio captured.")
			return np.array([])
		return audio
	except KeyboardInterrupt:
		print("keyboard Interrupt during recording!")
		return np.array([])


def transcribe_audio_with_openai(audio_data: np.ndarray, client, sample_rate: int = 48000) -> str:
	# Save audio to temporary WAV file (OpenAI STT requires a file upload)
	with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
		sf.write(tmpfile.name, audio_data, sample_rate)
		tmpfile.flush()
		# Call OpenAI Whisper API (note: model is "whisper-1")
		with open(tmpfile.name, "rb") as audio_file:
			transcript = client.audio.transcriptions.create(
                	model="whisper-1",
                	file=audio_file,
                	language="en"
			)

	return transcript.text

def handle_motor(action, value):
	ser = serial.Serial('/dev/ttyAMA0', baudrate = 115200, timeout = 1)
	try:
		speed = min(7 , max(value, 0))
		if value > 0: dir = 0
		else: dir = 1
		if action == "speed":
			# send value to mcu 
			m1 = dir << 3 | speed
			m2 = dir << 3 | speed
		elif action == "rotate":
			m1 = dir << 3 | speed
			m2 = (~dir & 1) | speed
		data = (m1 << 4) | m2
		ser.write(bytes([data]))
	except KeyboardInterrupt:
		print("keyboard Interrupt during listen_transcribe_respond function!")
def listen_transcribe_respond(gpt_client, deepseek_client, gcp_client, in_index ,out_index, voice, audio_config):
	try:
	# Record audio
		audio = record_until_silence(in_index)
		if audio is None or audio.size == 0:
			print("No valid audio to process. Exiting.")
			return
		audio /= np.max(np.abs(audio) + 1e-9)  # normalize to [-1, 1]

	# Whisper expects int16 or float32 in a numpy array
		transcription = transcribe_audio_with_openai(audio, gpt_client)
		print(f"User: {transcription}")

	# Send to DeepSeek (replace with actual API call)
		deepseek_response = get_output(transcription, deepseek_client)
		if deepseek_response[0] == '{':
			parsed_json = json.loads(deepseek_response)
			for cmd in parsed_json["commands"]:
				if cmd["device"] == "motor":
					handle_motor(cmd["action"], cmd["value"])
				elif cmd["device"] == "camera":
					handle_camera(cmd["action"], cmd["value"])
		else:
			# Speak it aloud
			speak_with_gcp(deepseek_response, out_index, gcp_client, voice, audio_config)
		print(f"AI: {deepseek_response}")

	except KeyboardInterrupt:
		print("keyboard Interrupt during listen_transcribe_respond function!")
