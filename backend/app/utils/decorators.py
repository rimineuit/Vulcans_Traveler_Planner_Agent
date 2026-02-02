from functools import wraps

def mongo_serialized(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        if result is None:
            return None
        
        # Logic chuyển đổi ObjectId
        if isinstance(result, list):
            for item in result:
                if "_id" in item:
                    item["_id"] = str(item["_id"])
        elif isinstance(result, dict):
            if "_id" in result:
                result["_id"] = str(result["_id"])
        return result
    return wrapper