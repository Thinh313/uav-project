# CLOCKPIPE09: read-only collection and durable authority

Root L2 authorized this isolated change after the R06 original trace showed a
110.501 ms clock-poll gap followed by a 118.646 ms durable TICK append before
query 939 could be sent. The old 938 reference reached 285.473 ms and the
unchanged 250 ms guard correctly rejected an unadmitted servo. The append's
non-CPU time is not proof of filesystem latency rather than descheduling.

The old candidate, R06, all earlier candidates and ENDURE remain immutable.
This new provider uses one socket/scheduler thread and one ordered clock writer
inside the existing backend process. The clock request period remains 100 ms,
pending requests remain at most eight, and the original total event/byte/case
limits remain unchanged. The queue has at most 64 total entries including the
entry popped by the writer, each with at most 2,048 serialized data bytes.

The explicit contract change applies only to read-only UDP time probes. Their
original TICK and REGISTERED events can be staged and the probe sent before
those events finish fsync. The inherited correlator algorithm is therefore
named TentativeCorrelator in this path. Its memory state, responses and
calibration output carry no authority. It does not use the original correlator's
durable-sink promise as a publication claim. The durable writer retains every
original event in exact order, then the matched RESPONSE and CLOCK_PUBLICATION.
Only after both return from the original journal fsync barriers may an immutable
Publication become visible. Its age is always measured from the original
userspace recvmsg return, never the later writer or publication time.

No MAVLink flight command, sensor transmission or input grant gains a similar
exception. The original sensor INTENT still finishes fsync before send. Every
entry and atomic send check retains the 250 ms clock freshness limit. True
faults latch before optional diagnostic IO; queue failures also block the
inherited dispatch path during the queue-to-owner failure transition.

Before any journal/frame/model admission, one original servo can wait at most
100 ms for a strictly newer durable publication, only while the ordered writer
has pending work. The wait is further bounded by the original case/servo
deadlines, original receive plus 500 ms, and previous sensor send plus 500 ms.
It never clears a failure, resets a clock, replays a frame, sends again, changes
speedup/cap or discards an accepted frame. After INTENT/model admission there is
no clock wait or retry: an expired reference rejects the send as before.

STAGE semantics are version 9. `receiveSinceOriginNs` and
`originalReceiveSinceOriginNs` retain the original recvmsg timestamp. Clock
proof fields now say `AtAdmission`, not `AtReceive`; admission may occur after
the packet receipt. `clockAtOriginalReceiptStatus=0` means UNKNOWN, not zero age
or an earlier permit. Separate admission time, bounded wait and prior
publication ID support cold checks of the new reference. API-entry mock calls
have receive-kind zero; actual backend receipt-kind one is mandatory for
acceptance. The cold reader checks these fields and the unchanged final send
publication/atomic permit ages.

Normal close and failure close retain bounded original os.write/fsync wall and
thread-CPU subspans in the existing 32 KiB clock diagnostic. They do not identify
the OS wait reason. Socket ingress stops before the writer drains; EIO,
overflow, wrong context, deadline and incomplete close remain failed with
uncommitted work explicitly UNKNOWN. No process, origin, source namespace,
metadata owner or numeric resource limit is added or enlarged.

Source/mock results are separate from Android-SITL acceptance. The independent
earlier Android codec error is a different Product repair. The newly identified
full-case physics quota/export capacity question must also close before either
remaining actual slot is used.
