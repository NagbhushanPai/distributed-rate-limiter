"""Load testing with Locust"""

from locust import HttpUser, task, between
import random


class RateLimiterUser(HttpUser):
    """Simulated user for load testing"""
    wait_time = between(0.1, 0.5)
    
    @task(3)
    def check_rate_limit(self):
        """Test /allow endpoint"""
        user_id = f"user_{random.randint(1, 100)}"
        self.client.post(
            '/allow',
            params={'user_id': user_id, 'tokens': 1}
        )
    
    @task(1)
    def get_status(self):
        """Test /status endpoint"""
        user_id = f"user_{random.randint(1, 100)}"
        self.client.get(
            '/status',
            params={'user_id': user_id}
        )
    
    @task(1)
    def health_check(self):
        """Test /health endpoint"""
        self.client.get('/health')
