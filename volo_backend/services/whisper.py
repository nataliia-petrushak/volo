from loguru import logger
from typing import Generator  # async?

from services.asr import OnlineASRProcessor, FasterWhisperASR


class WhisperService:
    def __init__(self, language: str = "en", model: str = "large-v2", min_chunk: int = 1):
        self.language = language
        self.model = model
        self.min_chunk = min_chunk
        self.asr = FasterWhisperASR(self.language, self.model)
        self.online = OnlineASRProcessor(self.asr)
        self.is_first = True
        self.sampling_rate = 16000
        self.processed = []

    # def audio_callback(self, indata, frames, time, status) -> None:
    #     """
    #     Callback function to continuously process audio chunks.
    #     """
    #     if status:
    #         print(f"Status: {status}")

    #     audio_chunk = indata[:, 0]
    #     self.online.insert_audio_chunk(audio_chunk)

    #     result = self.online.process_iter()
    #     if result is not None:
    #         self.processed.append(result)
    #         logger.debug(result)

    # add self.websocket to get audio inside func
    def process_stream(self, audio_stream: Generator[bytes, None, None]) -> str:
        """
        Process audio stream in real-time.
        """
        self.processed = []
        self.online.init()

        for audio_chunk in audio_stream:
            self.online.insert_audio_chunk(audio_chunk)

            result = self.online.process_iter()
            if result is not None:
                self.processed.append(result)
                logger.debug(result)
        
        self.online.finish()
        print("".join(self.processed))
        return "".join(self.processed)
        
        
        # print("Start speaking. Press Ctrl+C to stop.")
        # try:
        #     with sd.InputStream(samplerate=self.sampling_rate, channels=1, callback=self.audio_callback,
        #                         dtype=np.float32):
        #         while True:
        #             time.sleep(0.1)

        # except KeyboardInterrupt:
        #     print("Stopping...")

        # finally:
        #     result = []
        #     # TODO check if this even works (what's a buffer?)
        #     while len(self.online.audio_buffer) != 0:
        #         result = self.online.process_iter()
        #         self.processed.append(result)
        #         logger.debug(result)
        #     if not result:
        #         result = self.online.finish()
        #         self.processed.append(result)
        #     logger.debug(result)
        #     return "".join(self.processed)


# NOTE remove after testing
# if __name__ == '__main__':
#     processor = WhisperProcessor(lang="en", model="large-v2", min_chunk=5)
#     processor.process_stream()
