import sys
from loguru import logger


class HypothesisBuffer:

    def __init__(self, log_file=sys.stderr):
        self.saved_in_buffer = []
        self.buffer = []
        self.new = []

        self.last_saved_time = 0
        self.last_saved_word = None

        self.logfile = log_file

    def insert(self, new, offset) -> None:
        # compare self.saved_in_buffer and new. It inserts only the words in new that extend the saved_in_buffer,
        # it means they are roughly behind last_saved_time and new in content
        # the new tail is added to self.new

        new = [(a + offset, b + offset, t) for a, b, t in new]
        self.new = [(a, b, t) for a, b, t in new if a > self.last_saved_time - 0.1]

        if len(self.new) >= 1:
            a, b, t = self.new[0]
            if abs(a - self.last_saved_time) < 1:
                if self.saved_in_buffer:
                    # it's going to search for 1, 2, ..., 5 consecutive words (n-grams)
                    # that are identical in saved and new. If they are, they're dropped.
                    cn = len(self.saved_in_buffer)
                    nn = len(self.new)
                    for i in range(1, min(min(cn, nn), 5) + 1):  # 5 is the maximum 
                        c = " ".join([self.saved_in_buffer[-j][2] for j in range(1, i + 1)][::-1])
                        tail = " ".join(self.new[j - 1][2] for j in range(1, i + 1))
                        if c == tail:
                            words = []
                            for j in range(i):
                                words.append(repr(self.new.pop(0)))
                            words_msg = " ".join(words)
                            logger.debug(f"Removing last {i} words: {words_msg}")
                            break

    def flush(self) -> list:
        # returns saved chunk = the longest common prefix of 2 last inserts. 

        commit = []
        while self.new:
            na, nb, nt = self.new[0]

            if len(self.buffer) == 0:
                break

            if nt == self.buffer[0][2]:
                commit.append((na, nb, nt))
                self.last_saved_word = nt
                self.last_saved_time = nb
                self.buffer.pop(0)
                self.new.pop(0)
            else:
                break
        self.buffer = self.new
        self.new = []
        self.saved_in_buffer.extend(commit)
        return commit

    def pop_saved(self, time):
        while self.saved_in_buffer and self.saved_in_buffer[0][1] <= time:
            self.saved_in_buffer.pop(0)

    def complete(self):
        return self.buffer
