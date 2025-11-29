/glade/u/home/jjeffree/ensemble-analogue-predictability/analogue_forecasting_saveall.py:135: UserWarning: Attempting to calculate /glade/work/jjeffree/results/area/base/detail/composite_5_IPSL-CM6A-L_nomean_tos_zos/10P_12m2varagreement30A_I1_L0_3.nc
  warnings.warn('Attempting to calculate ' + out_filename)
Traceback (most recent call last):
  File "/glade/u/home/jjeffree/ensemble-analogue-predictability/analogue_forecasting_saveall.py", line 146, in <module>
    obs_pca = obs_pca_trim(obs_pca)
              ^^^^^^^^^^^^^^^^^^^^^
  File "/glade/u/home/jjeffree/ensemble-analogue-predictability/analogue_forecasting_saveall.py", line 111, in <lambda>
    obs_pca_trim = lambda x: x.sel(time=args.analogue_time_slice[data_name]).rename({'SMILE_M':'pred_SMILE_M'})
                                        ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
KeyError: 'composite_5'
2025-02-06 16:24:51,881 - distributed.worker - ERROR - Failed to communicate with scheduler during heartbeat.
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
distributed.comm.core.CommClosedError: in <TCP (closed) ConnectionPool.heartbeat_worker local=tcp://127.0.0.1:41098 remote=tcp://127.0.0.1:43681>: Stream is closed
