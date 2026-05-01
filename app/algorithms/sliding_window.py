"""Sliding Window Algorithm (Optional, for future use)"""


class SlidingWindow:
    """
    Sliding Window rate limiter (alternative to Token Bucket).
    
    Maintains a window of requests and counts within it.
    More strict than Token Bucket, but no burst support.
    """
    
    def __init__(self, requests_per_window, window_seconds):
        """
        Args:
            requests_per_window (int): Max requests allowed per window
            window_seconds (int): Window size in seconds
        """
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.requests = []
    
    def allow_request(self, current_time):
        """Check if request is allowed"""
        # Remove requests outside window
        cutoff = current_time - self.window_seconds
        self.requests = [t for t in self.requests if t > cutoff]
        
        # Check limit
        allowed = len(self.requests) < self.requests_per_window
        
        if allowed:
            self.requests.append(current_time)
        
        return {
            "allowed": allowed,
            "remaining_requests": max(0, self.requests_per_window - len(self.requests))
        }
