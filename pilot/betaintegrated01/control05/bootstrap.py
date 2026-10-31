"""Source-declared SiK reset startup envelope, never generic MAVLink resync."""
class StartupEnvelope:
    max_pairs=3
    incomplete_pair_max_ns=200_000_000
    def __init__(self):self.pairs=0;self.pending_ns=None;self.mav_started=False;self.last_ns=-1
    def tick(self,now_ns):
        if type(now_ns)is not int or now_ns<self.last_ns:raise ValueError('BOOTSTRAP_CLOCK_REGRESSION')
        self.last_ns=now_ns
        if self.pending_ns is not None and now_ns-self.pending_ns>self.incomplete_pair_max_ns:raise ValueError('BOOTSTRAP_INCOMPLETE_PAIR_200MS')
    def feed(self,raw,now_ns):
        self.tick(now_ns)
        if type(raw)is not bytes or len(raw)>4096:raise ValueError('BOOTSTRAP_RAW_BOUND')
        if self.mav_started:return raw,[]
        classified=[]
        for index,byte in enumerate(raw):
            if self.pending_ns is not None:
                if byte!=0x20:raise ValueError('BOOTSTRAP_EXACT_3020_PAIR_REQUIRED')
                self.pairs+=1;self.pending_ns=None
                classified.append({'pair':self.pairs,'rawHex':'3020','applicationTXBytes':0,'classification':'SITL_GCS_INIT_SIK_RESET_NOT_MAVLINK','hostNs':now_ns})
            elif byte in(0xfd,0xfe):
                self.mav_started=True;return raw[index:],classified
            elif byte==0x30 and self.pairs<self.max_pairs:self.pending_ns=now_ns
            else:raise ValueError('BOOTSTRAP_UNRECOGNIZED_OR_MORE_THAN_3_PAIRS')
        return b'',classified
