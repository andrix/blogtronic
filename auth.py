import hmac
import random
import string
import hashlib
import re

# securtiy
secret = "f65a001419b5149599b979c42a0c4ba13908e9ec~2305d500fd"

def make_secure_val(val):
    return "%s|%s" % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val, _ = secure_val.split("|")
    if secure_val == make_secure_val(val):
        return val

def make_salt(length=5):
    return "".join(random.choice(string.letters) for _ in range(length))

def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return "%s|%s" % (salt, h)

def valid_pw(name, password, h):
    salt, _ = h.split("|")
    return h == make_pw_hash(name, password, salt)
