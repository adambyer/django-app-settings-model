import json

from django.db import models
from django.db.utils import ProgrammingError
from django.conf import settings
from django.core.cache import cache as django_cache

from apps.utils.base_model import BaseModel


class AppSetting(BaseModel):
    CACHE_KEY = 'app-settings'

    class Meta:
        verbose_name_plural = 'App Settings'
        ordering = ('key',)

    key = models.CharField(max_length=50, unique=True)
    value = models.CharField(max_length=1000, blank=True)
    enabled = models.BooleanField(default=True)

    @classmethod
    def delete_cache(cls):
        django_cache.delete(cls.CACHE_KEY)

    @classmethod
    def get(cls, key, *args):
        """
        args[0] is optional default return value
        """
        data = django_cache.get(cls.CACHE_KEY)

        if not data:
            """
            before initial migration, AppSetting table will not exist (i.e. during docker build).
            just ignore.
            """
            try:
                data = {s.key: s.value for s in cls.objects.filter(enabled=True)}
                django_cache.set(cls.CACHE_KEY, data)
            except ProgrammingError:
                return None

        if key in data:
            value = data[key]
            return cls._typeify(value)
        else:
            if hasattr(settings, key):
                return getattr(settings, key)
            elif len(args):
                return args[0]
            else:
                raise AppSetting.DoesNotExist

    @classmethod
    def _typeify(cls, string_value):
        try:
            int(string_value)
            return int(string_value)
        except ValueError:
            pass

        if string_value.lower() == 'true':
            return True

        if string_value.lower() == 'false':
            return False

        if string_value.lower() == 'none':
            return None

        try:
            struct = json.loads(string_value)
            return struct
        except ValueError:
            pass

        return string_value
