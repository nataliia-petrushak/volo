from faster_whisper import FasterWhisper

model_size = "tiny"

model = WhisperModel(model_size, device="cpu", compute_type="int8")

