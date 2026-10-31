"""Independent host process wake proxy; no flight authority or trace writes until close."""
from pathlib import Path
import signal,sys,threading,time
from instrument import WakeProbe
out=Path(sys.argv[1]);probe=WakeProbe();done=threading.Event()
signal.signal(signal.SIGTERM,lambda *_:done.set());signal.signal(signal.SIGINT,lambda *_:done.set())
probe.start();done.wait(155);probe.seal(out/'wake-process.bin')
