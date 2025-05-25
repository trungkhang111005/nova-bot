import ctypes

class PaAlsaStreamInfo(ctypes.Structure):
	_fields_ = [
		('size', ctypes.c_uint32),
		('hostApiType', ctypes.c_uint32),
		('version', ctypes.c_uint32),
		('device_string', ctypes.c_char_p),
		('flags', ctypes.c_uint32),
	]

def build_alsa_info(device_str: str) -> PaAlsaStreamInfo:
	info = PaAlsaStreamInfo()
	info.size = ctypes.sizeof(PaAlsaStreamInfo)
	info.hostApiType = 8        # paALSA = 8
	info.version = 1
	if isinstance(device_str, str):
		info.device_string = device_str.encode()
	else:
		info.device_string = device_str  # already bytes

	info.flags = 0
	return info   # needed for PyAudio
