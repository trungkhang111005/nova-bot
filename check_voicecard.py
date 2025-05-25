import subprocess, re, ctypes, pyaudio

def pcm_from_arecord(card_hint: str) -> str:
        """Return 'plughw:<card>,<dev>' for the first card whose name contains *card_hint*."""
        txt = subprocess.check_output(['arecord', '-l'], text=True)
        # look for: card N: <id> [...] device M:
        pat = re.compile(r'card (\d+): ([^\s]+).*device (\d+):', re.S|re.I)
        for card, card_id, dev in pat.findall(txt):
                if card_hint.lower() in card_id.lower():
                        return f'plughw:{card},{dev}'
        raise RuntimeError(f'No capture card containing “{card_hint}” found')
card_hint='sndrpigooglevoi'
pcm = pcm_from_arecord(card_hint)
print(f"{pcm}")

