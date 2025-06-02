import gc
import os
import signal


def kill_process():
    print("Killing process...")
    os.kill(os.getpid(), signal.SIGTERM)

def gc_collect():
    gc.collect()