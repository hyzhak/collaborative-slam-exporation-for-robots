import time

def send_command(client, stream, command_data):
    """
    XADD a command to the specified stream.
    Returns the message ID.
    """
    return client.xadd(stream, command_data)

def collect_events(client, reply_stream, group, consumer, correlation_id, timeout=5.0):
    """
    XREADGROUP from reply_stream, collecting events for the given correlation_id.
    Returns a list of status values in the order received.
    """
    events = []
    start_time = time.time()
    print('Collecting events from stream:', reply_stream)
    while time.time() - start_time < timeout:
        resp = client.xreadgroup(
            groupname=group,
            consumername=consumer,
            streams={reply_stream: ">"},
            count=10,
            block=500,
        )
        for sname, messages in resp:
            for msg_id, msg in messages:
                if msg.get("correlation_id") == correlation_id and "status" in msg:
                    try:
                        client.xack(reply_stream, group, msg_id)
                        print(f"Acknowledged message {msg_id}")
                    except Exception as ack_err:
                        print(f"Failed to acknowledge message {msg_id}: {ack_err}")
                    events.append(msg["status"])
        if "completed" in events:
            break
    print(f"Collected events: {events}")
    return events
