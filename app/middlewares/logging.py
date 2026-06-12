import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f} sec"
        print(f"🚀 [Log] {request.method} | {request.url.path} | {process_time:.4f} sec")
        return response
