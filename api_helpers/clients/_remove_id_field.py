def _remove_id_field(obj):
    if obj is None:
        return
    if '_id' in obj:
        del obj['_id']
