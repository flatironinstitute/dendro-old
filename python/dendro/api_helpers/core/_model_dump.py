def _model_dump(model, exclude_none=False):
    # handle both pydantic v1 and v2
    if hasattr(model, 'model_dump'):
        return model.model_dump(exclude_none=exclude_none)
    else:
        return model.dict(exclude_none=exclude_none)
