import sys
from abc import ABC, abstractmethod


class ASRBase(ABC):
    # join transcribe words with this character (" " for whisper_timestamped,
    # "" for faster-whisper because it emits the spaces when needed)
    separator = " "

    def __init__(
            self, language: str, model_size=None, cache_dir=None, model_dir=None, log_file=sys.stderr
    ) -> None:
        self.logfile = log_file

        self.transcribe_kwargs = {}
        if language == "auto":
            self.language = None
        else:
            self.language = language

        self.model = self.load_model(model_size, cache_dir, model_dir)

    @abstractmethod
    def load_model(self, model_size, cache_dir, model_dir):
        pass

    @abstractmethod
    def transcribe(self, audio, init_prompt: str = ""):
        pass

    @abstractmethod
    def use_vad(self):
        pass
