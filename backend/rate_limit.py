"""
Rate limiting partagé (slowapi) — protège les routes sensibles de auth contre
le bruteforce et le spam (login, inscription, reset de mot de passe).

Stockage en mémoire du process (par défaut slowapi) : suffisant pour une
seule instance Railway. Si l'app scale un jour sur plusieurs instances, il
faudra un stockage partagé (Redis) pour que la limite reste globale.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
