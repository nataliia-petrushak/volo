from loguru import logger
from services import OnlineASRProcessor, FasterWhisperASR


class StreamingService:

    def __init__(self, websocket, min_chunk=0.3):
        self.connection = websocket
        self.asr = FasterWhisperASR(language="en", model_size="tiny")
        self.online_asr_proc = OnlineASRProcessor(asr=self.asr)
        self.min_chunk = min_chunk
        self.last_end = None
        self.is_first = True

    async def receive_audio_chunk(self):
        # receive all audio that is available by this time
        # blocks operation if less than self.min_chunk seconds is available
        # unblocks if connection is closed or a chunk is available
        out = b""
        min_limit = self.min_chunk * 16000

        while len(out) < min_limit:
            raw_bytes = await self.connection.receive()
            if "bytes" not in raw_bytes:
                break
            out += raw_bytes["bytes"]

        if not out:
            return None
        if self.is_first and len(out) < min_limit:
            return None
        self.is_first = False
        return out

    async def process(self):
        # handle one client connection
        self.online_asr_proc.init()
        while True:
            audio = await self.receive_audio_chunk()
            if audio is None:
                break
            self.online_asr_proc.insert_audio_chunk(audio)
            output = self.online_asr_proc.process_iter()
            try:
                yield output
            except BrokenPipeError:
                logger.info("broken pipe -- connection closed?")
                break
        output = self.online_asr_proc.finish()
        yield output
