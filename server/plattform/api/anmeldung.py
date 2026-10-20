# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Anmeldung der internen Anwendung (ADR-0003 Nr. 10: ein Konto, Anmeldung auch im Heimnetz).

* Passwort nur als scrypt-Hash in der lokalen Konfiguration (plattform_config.toml, nicht im Repo).
* Sitzung als signiertes Cookie (HMAC-SHA256, Ablaufzeit im Wert): kein Sitzungsspeicher nötig.
  Abmelden löscht das Cookie; alle Sitzungen beendet ein neuer Sitzungsschlüssel.
* Bremse gegen Durchprobieren: nach 5 Fehlversuchen je Adresse 60 s Sperre.
Ohne Datenbank testbar. Hash erzeugen:  python3 -m api.anmeldung   (im Ordner server/plattform)
"""
import base64
import hashlib
import hmac
import secrets
import threading
import time

COOKIE = "bienen_sitzung"
_N, _R, _P = 2 ** 14, 8, 1


def _b64(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def passwort_hash(passwort, salz=None):
    salz = salz or secrets.token_bytes(16)
    h = hashlib.scrypt(passwort.encode(), salt=salz, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${_b64(salz)}${_b64(h)}"


def passwort_pruefen(passwort, gespeichert):
    try:
        art, n, r, p, salz, soll = gespeichert.split("$")
        if art != "scrypt":
            return False
        ist = hashlib.scrypt(passwort.encode(), salt=_unb64(salz), n=int(n), r=int(r), p=int(p), dklen=len(_unb64(soll)))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(ist, _unb64(soll))


def _signatur(schluessel, inhalt):
    return _b64(hmac.new(schluessel.encode(), inhalt.encode(), hashlib.sha256).digest())


def sitzung_erzeugen(schluessel, dauer_s, jetzt=None):
    ablauf = int((jetzt if jetzt is not None else time.time()) + dauer_s)
    inhalt = f"v1.{ablauf}.{secrets.token_urlsafe(12)}"
    return f"{inhalt}.{_signatur(schluessel, inhalt)}"


def sitzung_gueltig(schluessel, wert, jetzt=None):
    if not isinstance(wert, str) or wert.count(".") != 3:
        return False
    inhalt, sig = wert.rsplit(".", 1)
    if not hmac.compare_digest(sig, _signatur(schluessel, inhalt)):
        return False
    try:
        ablauf = int(inhalt.split(".")[1])
    except ValueError:
        return False
    return (jetzt if jetzt is not None else time.time()) < ablauf


class Bremse:
    """Versuche je Adresse; nach max_fehler erfolglosen Versuchen sperrt sie für sperre_s Sekunden.

    versuch() prüft und zählt in einem Schritt unter einer Sperre, bevor das Passwort geprüft wird. So helfen auch
    viele gleichzeitige Anfragen (FastAPI bedient sie parallel im Threadpool) nicht über die Grenze hinweg.
    Erst ein Erfolg setzt den Zähler zurück.
    """

    def __init__(self, max_fehler=5, sperre_s=60):
        self.max_fehler, self.sperre_s = max_fehler, sperre_s
        self.zaehler = {}           # Adresse → (Anzahl Versuche ohne Erfolg, Zeit des letzten Versuchs)
        self.sperre = threading.Lock()

    def versuch(self, adresse, jetzt=None):
        """True: Versuch erlaubt und schon gezählt. False: gesperrt."""
        jetzt = jetzt if jetzt is not None else time.time()
        with self.sperre:
            n, t = self.zaehler.get(adresse, (0, 0))
            if n >= self.max_fehler:
                if jetzt - t < self.sperre_s:
                    return False
                n = 0
            self.zaehler[adresse] = (n + 1, jetzt)
            return True

    def erfolg(self, adresse):
        with self.sperre:
            self.zaehler.pop(adresse, None)


if __name__ == "__main__":
    import getpass
    pw = getpass.getpass("Neues Passwort: ")
    if pw != getpass.getpass("Wiederholen: ") or len(pw) < 10:
        raise SystemExit("Passwörter verschieden oder kürzer als 10 Zeichen")
    print("passwort_hash =", repr(passwort_hash(pw)))
    print("sitzungsschluessel =", repr(secrets.token_urlsafe(32)))
