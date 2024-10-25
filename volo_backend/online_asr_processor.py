import sys
import tokenize_uk

import numpy as np
from loguru import logger
from mosestokenizer import MosesTokenizer
from wtpsplit import WtP

from .hypotesis_buffer import HypothesisBuffer
from core import config


class UkrainianTokenizer:
    @staticmethod
    def split(text):
        return tokenize_uk.tokenize_sents(text)


class WtPtok:
    def __init__(self, language: str | None) -> None:
        self.language = language
        self.wtp = WtP("wtp-canine-s-12l-no-adapters")

    def split(self, sent):
        return self.wtp.split(sent, lang_code=self.language)


class OnlineASRProcessor:
    SAMPLING_RATE = 16000

    def __init__(self, asr, buffer_trimming=("segment", 15), log_file=sys.stderr):
        """
        asr: WhisperASR object
        tokenizer: sentence tokenizer object for the target language. Must have a method *split* that
                   behaves like the one of MosesTokenizer. It can be None, if "segment" buffer
                   trimming option is used, then tokenizer is not used at all.
                  ("segment", 15)
        buffer_trimming: a pair of (option, seconds), where option is either "sentence" or
                         "segment", and seconds is a number. Buffer is trimmed if it is longer than "seconds" threshold.
                         Default is the most recommended option.
        logfile: where to store the log.
        """
        self.asr = asr
        self.tokenizer = self.create_tokenizer()
        self.log_file = log_file
        self.audio_buffer = None
        self.transcript_buffer = None
        self.buffer_time_offset = None
        self.committed = None

        self.init()

        self.buffer_trimming_way, self.buffer_trimming_sec = buffer_trimming

    def init(self, offset=None):
        """Run this when starting or restarting processing"""
        self.audio_buffer = np.array([], dtype=np.float32)
        self.transcript_buffer = HypothesisBuffer(log_file=self.log_file)
        self.buffer_time_offset = 0
        if offset is not None:
            self.buffer_time_offset = offset
        self.transcript_buffer.last_saved_time = self.buffer_time_offset
        self.committed = []

    def create_tokenizer(self):
        """returns an object that has split function that works like the one of MosesTokenizer"""

        if self.asr.language not in config.WHISPER_LANG_CODES:
            raise ValueError("language must be Whisper's supported lang code: " + " ".join(config.WHISPER_LANG_CODES))

        if self.asr.language == "uk":
            return UkrainianTokenizer()

        # supported by fast-mosestokenizer
        if self.asr.language in (
                "as bn ca cs de el en es et fi fr ga gu hi hu is it kn lt "
                "lv ml mni mr nl or pa pl pt ro ru sk sl sv ta te yue zh"
        ):

            return MosesTokenizer(self.asr.language)

        if self.asr.language in "as ba bo br bs fo haw hr ht jw lb ln lo mi nn oc sa sd sn so su sw tk tl tt":
            logger.debug(f"{self.asr.language} code is not supported by wtpsplit. Going to use None lang_code option.")
            self.asr.language = None

        # downloads the model from huggingface on the first use
        return WtPtok(language=self.asr.language)

    def insert_audio_chunk(self, audio):
        self.audio_buffer = np.append(self.audio_buffer, audio)

    def prompt(self) -> tuple:
        """Returns a tuple: (prompt, context), where "prompt" is a 200-character suffix of committed text that
        is inside the scrolled away part of audio buffer. "context" is the committed text that is inside the
        audio buffer. It is transcribed again and skipped. It is returned only for debugging and logging reasons.
        """
        k = max(0, len(self.committed) - 1)
        while k > 0 and self.committed[k - 1][1] > self.buffer_time_offset:
            k -= 1

        p = self.committed[:k]
        p = [t for _, _, t in p]
        prompt = []
        l = 0
        while p and l < 200:  # 200 characters prompt size
            x = p.pop(-1)
            l += len(x) + 1
            prompt.append(x)
        non_prompt = self.committed[k:]
        return self.asr.seperator.join(prompt[::-1]), self.asr.seperator.join(t for _, _, t in non_prompt)

    def process_iter(self):
        """Runs on the current audio buffer.
        Returns: a tuple (beg_timestamp, end_timestamp, "text"), or (None, None, "").
        The non-empty text is confirmed (committed) partial transcript.
        """
        prompt, non_prompt = self.prompt()
        logger.debug(f"PROMPT: {prompt}")
        logger.debug(f"CONTEXT: {non_prompt}")
        logger.warning(len(self.audio_buffer))
        logger.debug(
            f"transcribing {len(self.audio_buffer) / self.SAMPLING_RATE:2.2f} seconds from {self.buffer_time_offset:2.2f}")
        res = self.asr.transcribe(self.audio_buffer, init_prompt=prompt)

        # transform to [(beg,end,"word1"), ...]
        timestamped_words = self.asr.ts_words(res)

        self.transcript_buffer.insert(timestamped_words, self.buffer_time_offset)
        o = self.transcript_buffer.flush()
        self.committed.extend(o)
        completed = self.to_flush(o)
        logger.debug(f">>>>COMPLETE NOW: {completed}")
        # the_rest = self.to_flush(self.transcript_buffer.complete())
        # logger.debug(f"INCOMPLETE: {the_rest}")

        # there is a newly confirmed text

        if o and self.buffer_trimming_way == "sentence":  # trim the completed sentences
            if len(self.audio_buffer) / self.SAMPLING_RATE > self.buffer_trimming_sec:  # longer than this
                self.chunk_completed_sentence()

        if self.buffer_trimming_way == "segment":
            s = self.buffer_trimming_sec  # trim the completed segments longer than s,
        else:
            s = 30  # if the audio buffer is longer than 30s, trim it

        if len(self.audio_buffer) / self.SAMPLING_RATE > s:
            self.chunk_completed_segment(res)

            # alternative: on any word
            # l = self.buffer_time_offset + len(self.audio_buffer)/self.SAMPLING_RATE - 10
            # let's find committed word that is less
            # k = len(self.committed)-1
            # while k>0 and self.committed[k][1] > l:
            #    k -= 1
            # t = self.committed[k][1]
            # logger.debug("chunking segment")
            # self.chunk_at(t)

        logger.debug(f"len of buffer now: {len(self.audio_buffer) / self.SAMPLING_RATE:2.2f}")
        return self.to_flush(o)

    def chunk_completed_sentence(self):
        if not self.committed:
            return
        logger.debug(self.committed)
        sentence = self.words_to_sentences(self.committed)
        for s in sentence:
            logger.debug(f"\t\tSENT: {s}")
        if len(sentence) < 2:
            return
        while len(sentence) > 2:
            sentence.pop(0)
        # we will continue with audio processing at this timestamp
        chunk_at = sentence[-2][1]

        logger.debug(f"--- sentence chunked at {chunk_at:2.2f}")
        self.chunk_at(chunk_at)

    def chunk_completed_segment(self, res):
        if not self.committed:
            return

        ends = self.asr.segments_end_ts(res)

        t = self.committed[-1][1]

        if len(ends) > 1:

            e = ends[-2] + self.buffer_time_offset
            while len(ends) > 2 and e > t:
                ends.pop(-1)
                e = ends[-2] + self.buffer_time_offset
            if e <= t:
                logger.debug(f"--- segment chunked at {e:2.2f}")
                self.chunk_at(e)
            else:
                logger.debug(f"--- last segment not within commited area")
        else:
            logger.debug(f"--- not enough segments to chunk")

    def chunk_at(self, time):
        """trims the hypothesis and audio buffer at 'time'"""
        self.transcript_buffer.pop_commited(time)
        cut_seconds = time - self.buffer_time_offset
        self.audio_buffer = self.audio_buffer[int(cut_seconds * self.SAMPLING_RATE):]
        self.buffer_time_offset = time

    def words_to_sentences(self, words):
        """Uses self.tokenizer for sentence segmentation of words.
        Returns: [(beg,end,"sentence 1"),...]
        """

        cwords = [w for w in words]
        t = " ".join(o[2] for o in cwords)
        s = self.tokenizer.split(t)
        out = []
        while s:
            beg = None
            end = None
            sent = s.pop(0).strip()
            fsent = sent
            while cwords:
                b, e, w = cwords.pop(0)
                w = w.strip()
                if beg is None and sent.startswith(w):
                    beg = b
                elif end is None and sent == w:
                    end = e
                    out.append((beg, end, fsent))
                    break
                sent = sent[len(w):].strip()
        return out

    def finish(self):
        """Flush the incomplete text when the whole processing ends.
        Returns: the same format as self.process_iter()
        """
        o = self.transcript_buffer.complete()
        f = self.to_flush(o)
        logger.debug(f"last, not committed: {f}")
        self.buffer_time_offset += len(self.audio_buffer) / 16000
        return f

    def to_flush(self, sentences, separator=None, offset=0, ) -> tuple:
        # Concatenates the timestamped words or sentences into one sequence that is flushed in one line
        # sentences: [(beg1, end1, "sentence1"), ...] or [] if empty
        # return: (beg1, end-of-last-sentence,"concatenation of sentences") or (None, None, "") if empty
        if separator is None:
            separator = self.asr.separator
        t = separator.join(s[2] for s in sentences)
        if len(sentences) == 0:
            b = None
            e = None
        else:
            b = offset + sentences[0][0]
            e = offset + sentences[-1][1]
        return b, e, t
