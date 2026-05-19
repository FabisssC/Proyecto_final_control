def apply_prop_fault(u_prop_cmd, time_min, enabled=False, start_min=30.0, factor=0.7):
    u_prop_faulted = u_prop_cmd

    if enabled and time_min >= start_min:
        u_prop_faulted = factor * u_prop_cmd

    return u_prop_faulted


def apply_remi_fault(u_remi_cmd, time_min, enabled=False, start_min=30.0, factor=0.7):
    u_remi_faulted = u_remi_cmd

    if enabled and time_min >= start_min:
        u_remi_faulted = factor * u_remi_cmd

    return u_remi_faulted