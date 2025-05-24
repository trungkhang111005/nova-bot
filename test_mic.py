import sounddevice as sd
import numpy as np
import queue
import time
from scipy.io import wavfile

def rms(chunk):
	return np.sqrt(np.mean(chunk**2))

def record_until_silence(in_index: int, sample_rate=48000, threshold=0.0008, silence_duration=2.0, max_duration=15, chunk_duration=0.1):
	try:
		q_buffer = queue.Queue()
		speaking_started = False
		silence_start_time = None
		chunk_samples = int(sample_rate * chunk_duration)
		max_chunks = int(max_duration / chunk_duration)

		def callback(indata, frames, time_info, status):
			if status:
				print("Callback status:", status)
			print(f"Callback fired: {frames} frames, RMS: {rms(indata[:, 0])}")
			q_buffer.put(indata.copy())

		print("Listening...")
		buffer = []

		with sd.InputStream(samplerate=sample_rate, channels=1, device=in_index, dtype='float32',
		                    blocksize=chunk_samples, callback=callback):
			for _ in range(max_chunks):
				chunk = q_buffer.get()
				chunk = np.squeeze(chunk)

				if rms(chunk) >= threshold:
					speaking_started = True
					silence_start_time = None
				elif speaking_started:
					if silence_start_time is None:
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
		print("Keyboard Interrupt during recording!")
		return np.array([])

def save_and_play(audio_data, sample_rate=48000, out_index=1, filename="output.wav"):
	if audio_data.size == 0:
		print("Empty audio data; skipping save/play.")
		return

	# Normalize to int16 for WAV
	audio_int16 = np.int16(audio_data / np.max(np.abs(audio_data)) * 32767)
	wavfile.write(filename, sample_rate, audio_int16)
	print(f"Saved to {filename}")

	# Playback
	print("Playing back...")
	sd.play(audio_int16, samplerate=sample_rate, device=out_index)
	sd.wait()
	print("Playback finished.")

if __name__ == "__main__":
	IN_INDEX = 0  # adjust as needed
	OUT_INDEX = 1

	audio = record_until_silence(IN_INDEX)
	save_and_play(audio, out_index=OUT_INDEX)
