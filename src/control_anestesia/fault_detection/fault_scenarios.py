def apply_prop_fault(u_prop_cmd, time_min, enabled=False, start_min=30.0, factor=0.7):
    if enabled and time_min >= start_min:
        return factor * u_prop_cmd
    return u_prop_cmd


def apply_remi_fault(u_remi_cmd, time_min, enabled=False, start_min=30.0, factor=0.7):
    if enabled and time_min >= start_min:
        return factor * u_remi_cmd
    return u_remi_cmd