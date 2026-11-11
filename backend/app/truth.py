STATES = {'CONFIRMED', 'PENDING', 'UNKNOWN', 'FAILED'}
def derive_truth(resource: dict, previous='PENDING'):
    """Only call with an authenticated provider resource matching the order."""
    captures = [c for u in resource.get('purchase_units', []) for c in u.get('payments', {}).get('captures', [])]
    if any(c.get('status') == 'COMPLETED' for c in captures): return 'CONFIRMED'
    if previous == 'CONFIRMED': return previous
    if any(c.get('status') == 'PENDING' for c in captures): return 'PENDING'
    if captures and all(c.get('status') in ('DECLINED', 'DENIED', 'FAILED') for c in captures): return 'FAILED'
    return 'UNKNOWN' if not resource else 'PENDING'
def can_retry(state): return state == 'FAILED'
