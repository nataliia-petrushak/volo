import io

from faster_whisper import WhisperModel
from loguru import logger

from .asr_base import ASRBase


class FasterWhisperASR(ASRBase):
    """Uses faster-whisper library as the backend.
    Works much faster, appx 4-times (in offline mode).
    For GPU, it requires installation with a specific CUDNN version.
    """

    seperator = ""

    def load_model(self, model_size=None, cache_dir=None, model_dir=None):

        if model_dir is not None:
            logger.debug(
                f"Loading whisper model from model_dir {model_dir}. model_size and cache_dir parameters are not used."
            )
            model_size_or_path = model_dir
        elif model_size is not None:
            model_size_or_path = model_size
        else:
            raise ValueError("model_size or model_dir parameter must be set")

        # this worked fast and reliably on NVIDIA L40
        # model = WhisperModel(model_size_or_path, device="cuda", compute_type="float16", download_root=cache_dir)

        # or run on GPU with INT8
        # tested: the transcripts were different, probably worse than with FP16, and it was slightly (appx 20%) slower
        # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")

        # or run on CPU with INT8
        # tested: works, but slow, appx 10-times than cuda FP16, download_root="faster-disk-cache-dir/")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        return model

    def transcribe(self, audio, init_prompt: str = "") -> list:
        # tested: beam_size=5 is faster and better than 1 (on one 200 second document from En ESIC, min chunk 0.01)
        segments, info = self.model.transcribe(
            io.BytesIO(audio),
            language=self.language,
            initial_prompt=init_prompt,
            beam_size=3,
            word_timestamps=True,
            condition_on_previous_text=True,
            **self.transcribe_kwargs
        )
        return list(segments)

    @staticmethod
    def timestamped_words(segments):
        result = []
        for segment in segments:
            for word_item in segment.words:
                if segment.no_speech_prob > 0.9:
                    continue
                # not stripping the spaces -- should not be merged with them!
                word = word_item.word
                timestamped = (word_item.start, word_item.end, word)
                result.append(timestamped)
        return result

    @staticmethod
    def segments_end_ts(res):
        return [s.end for s in res]

    def use_vad(self):
        self.transcribe_kwargs["vad_filter"] = True

    def set_translate_task(self):
        self.transcribe_kwargs["task"] = "translate"
