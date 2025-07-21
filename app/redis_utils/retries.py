def immediate_fail_retry(attempt, elapsed, last_delay):
    """
    Retry strategy: fail immediately, no retries.
    """
    return None

def exponential_retry(initial=0.1, factor=2, max_delay=1.0, max_attempts=10):
    """
    Factory for exponential backoff retry strategy.
    Returns a function (attempt, elapsed, last_delay) -> delay or None.
    """

    def strategy(attempt, elapsed, last_delay):
        if attempt > max_attempts:
            return None
        try:
            delay = initial * (factor ** (attempt - 1))
        except OverflowError:
            return None
        return min(delay, max_delay)

    return strategy

def linear_retry(step=0.2, max_delay=1.0, max_attempts=10):
    """
    Factory for linear backoff retry strategy.
    Returns a function (attempt, elapsed, last_delay) -> delay or None.
    """

    def strategy(attempt, elapsed, last_delay):
        if attempt > max_attempts:
            return None
        try:
            delay = step * attempt
        except OverflowError:
            return None
        return min(delay, max_delay)

    return strategy
