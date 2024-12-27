from typing import Any

def handler(input: dict, context: object) -> dict[str, Any]:

    timestamp = input.get("timestamp", 0)
    bytes_sent = input.get("net_io_counters_eth0-bytes_sent", 0)
    bytes_recv = input.get("net_io_counters_eth0-bytes_recv", 0)
    memory_cached = input.get("virtual_memory-cached", 0)
    memory_buffers = input.get("virtual_memory-buffers", 0)
    memory_total = input.get("virtual_memory-total", 0)

    env = context.env

    percent_network_egress = (bytes_sent / (bytes_sent + bytes_recv)) * 100 if (bytes_sent + bytes_recv) > 0 else 0
    
    percent_memory_caching = ((memory_cached + memory_buffers) / memory_total) * 100 if memory_total > 0 else 0

    cpus = [key for key in input.keys() if key.startswith("cpu_percent-")]

    cpus_avg = {}

    for cpu_key in cpus:
        cpu_usage = input.get(cpu_key, 0)

        cpu_states = env.get(cpu_key, [])
        cpu_states.append(cpu_usage)

        if(len(cpu_states) > 12):
            cpu_states.pop(0)
        
        avg_usage = sum(cpu_states)/len(cpu_states)
        cpus_avg[f"{cpu_key}_avg"] = avg_usage
        env[f"{cpu_key}_avg"] = avg_usage
        env[cpu_key] = cpu_states
    
    output = {
        "timestamp": timestamp,
        "percent-network-egress": percent_network_egress,
        "percent-memory-caching": percent_memory_caching,
        'cpus_avg': cpus_avg
    }

    return output






