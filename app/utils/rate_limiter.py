"""Rate limiting utilities."""

import time
from typing import Dict, Optional
from fastapi import HTTPException, Request
import redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter using Redis for distributed rate limiting."""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url)
        self.rate_limit_per_minute = settings.rate_limit_per_minute
        self.rate_limit_burst = settings.rate_limit_burst
    
    async def check_rate_limit(self, 
                             request: Request, 
                             user_id: Optional[str] = None,
                             tenant_id: Optional[str] = None) -> bool:
        """Check if request is within rate limits."""
        
        # Create rate limit key
        if user_id:
            key = f"rate_limit:user:{user_id}"
        elif tenant_id:
            key = f"rate_limit:tenant:{tenant_id}"
        else:
            # Use IP address as fallback
            client_ip = request.client.host
            key = f"rate_limit:ip:{client_ip}"
        
        current_time = int(time.time())
        minute_window = current_time // 60
        
        # Use sliding window counter
        pipe = self.redis_client.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, minute_window - 1)
        
        # Count current requests
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(current_time): current_time})
        
        # Set expiration
        pipe.expire(key, 120)  # 2 minutes
        
        results = pipe.execute()
        current_count = results[1]
        
        # Check limits
        if current_count >= self.rate_limit_per_minute:
            logger.warning(f"Rate limit exceeded for {key}: {current_count}/{self.rate_limit_per_minute}")
            return False
        
        return True
    
    async def get_rate_limit_info(self, 
                                user_id: Optional[str] = None,
                                tenant_id: Optional[str] = None) -> Dict[str, int]:
        """Get current rate limit information."""
        
        if user_id:
            key = f"rate_limit:user:{user_id}"
        elif tenant_id:
            key = f"rate_limit:tenant:{tenant_id}"
        else:
            return {"limit": self.rate_limit_per_minute, "remaining": self.rate_limit_per_minute}
        
        current_time = int(time.time())
        minute_window = current_time // 60
        
        # Count current requests
        current_count = self.redis_client.zcount(key, minute_window, current_time)
        
        return {
            "limit": self.rate_limit_per_minute,
            "remaining": max(0, self.rate_limit_per_minute - current_count),
            "reset_time": (minute_window + 1) * 60
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit_middleware(request: Request, call_next):
    """Middleware to check rate limits."""
    
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    # Extract user info from request (this would be done by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", None)
    
    # Check rate limit
    if not await rate_limiter.check_rate_limit(request, user_id, tenant_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    return await call_next(request)
