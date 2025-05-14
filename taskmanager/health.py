from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from redis.exceptions import RedisError
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    """
    Basic health check that verifies database and cache connections
    """
    status = True
    redis_status = True
    db_status = True
    cache_status = True

    # Check database connection
    try:
        for name in connections:
            cursor = connections[name].cursor()
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            assert row is not None
    except OperationalError:
        db_status = False
        status = False
    
    # Check Redis connection
    try:
        cache_key = "health_check_test"
        cache.set(cache_key, "test_value", timeout=30)
        test_value = cache.get(cache_key)
        if test_value != "test_value":
            cache_status = False
            status = False
    except RedisError:
        redis_status = False
        status = False

    result = {
        'status': 'healthy' if status else 'unhealthy',
        'database': 'up' if db_status else 'down',
        'cache': 'up' if cache_status else 'down',
        'redis': 'up' if redis_status else 'down'
    }

    status_code = 200 if status else 503
    return JsonResponse(data=result, status=status_code)
