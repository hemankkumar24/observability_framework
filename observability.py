import time
from db import save_event

def trace_node(trace_id, node_name, func, state, retries=1):
    attempt = 0
    while attempt <= retries:
        start = time.time()
        success = True
        error = None

        try:
            new_state = func(state)
            end = time.time()
            save_event({
                "trace_id": trace_id,
                "node": node_name,
                "latency": round(end - start, 4),
                "success": 1,
                "error": None
            })
            return new_state
        except Exception as e:
            attempt += 1
            success = False
            error = str(e)
            end = time.time()

            save_event({
                "trace_id": trace_id,
                "node": node_name,
                "latency": round(end - start, 4),
                "success": 0,
                "error": error
            })

            if attempt > retries:
                return state