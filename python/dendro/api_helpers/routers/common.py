import traceback
from fastapi import HTTPException
from functools import wraps


class AuthException(Exception):
    pass

def api_route_wrapper(route_func):
    @wraps(route_func)
    async def wrapper(*args, **kwargs):
        try:
            return await route_func(*args, **kwargs)
        except AuthException as ae:
            raise HTTPException(status_code=401, detail=str(ae))
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e)) from e
    return wrapper
