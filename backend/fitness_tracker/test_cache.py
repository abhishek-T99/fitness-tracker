from django.core.cache.backends.locmem import LocMemCache


class PatternLocMemCache(LocMemCache):
    """
    LocMemCache extended with delete_pattern.

    django-redis exposes delete_pattern for wildcard invalidation; some app
    signals call it unconditionally. In tests we simply clear the whole cache
    so the signal can fire without erroring.
    """

    def delete_pattern(self, pattern, **kwargs):
        self.clear()
