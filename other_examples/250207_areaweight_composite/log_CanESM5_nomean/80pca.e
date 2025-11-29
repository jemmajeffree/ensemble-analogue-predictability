/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/distributed/node.py:182: UserWarning: Port 8787 is already in use.
Perhaps you already have a cluster running?
Hosting the HTTP server on port 33159 instead
  warnings.warn(
2025-02-06 16:23:22,515 - distributed.worker - ERROR - Failed to communicate with scheduler during heartbeat.
Traceback (most recent call last):
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/distributed/comm/tcp.py", line 225, in read
    frames_nosplit_nbytes_bin = await stream.read_bytes(fmt_size)
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tornado.iostream.StreamClosedError: Stream is closed

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/distributed/worker.py", line 1250, in heartbeat
    response = await retry_operation(
               ^^^^^^^^^^^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/distributed/utils_comm.py", line 459, in retry_operation
    return await retry(
           ^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/distributed/utils_comm.py", line 438, in retry
    return await coro()
           ^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/distributed/core.py", line 1254, in send_recv_from_rpc
    return await send_recv(comm=comm, op=key, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/distributed/core.py", line 1013, in send_recv
    response = await comm.read(deserializers=deserializers)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/distributed/comm/tcp.py", line 236, in read
    convert_stream_closed_error(self, e)
  File "/glade/work/jjeffree/conda-envs/jj_default2/lib/python3.12/site-packages/distributed/comm/tcp.py", line 142, in convert_stream_closed_error
    raise CommClosedError(f"in {obj}: {exc}") from exc
distributed.comm.core.CommClosedError: in <TCP (closed) ConnectionPool.heartbeat_worker local=tcp://127.0.0.1:42400 remote=tcp://127.0.0.1:36021>: Stream is closed
