import base64, platform, os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv
import win32crypt 

load_dotenv()
def _get_salt() -> bytes:
	# Use environment variable or generate a default salt	
	env_salt = os.getenv('LLM_PROVIDER_SALT')
	if env_salt:
		return env_salt.encode('utf-8')
	return b'llm_provider_default_salt_2025'

def derive_key_from_password(password: str) -> bytes:
	kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_get_salt(), iterations=100_000)
	return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def dpapi_protect(data: bytes, machine_scope: bool = False, entropy: str | None = None) -> bytes | None:
	if platform.system() != "Windows" or win32crypt is None:
		return None
	flags = 0x4 if machine_scope else 0
	try:
		ent = entropy.encode("utf-8") if entropy else None
		return win32crypt.CryptProtectData(data, None, ent, None, None, flags)  # type: ignore
	except Exception as e:
		print(e)
		return None

def dpapi_unprotect(blob: bytes, entropy: str | None = None) -> bytes | None:
	if platform.system() != "Windows" or win32crypt is None:
		return None
	try:
		ent = entropy.encode("utf-8") if entropy else None
		description, data = win32crypt.CryptUnprotectData(blob, ent, None, None, 0)  # type: ignore
		return data
	except Exception as e:
		print(e)
		return None