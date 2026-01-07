from typing import Dict, Tuple

try:
	import requests
except ImportError:
	requests = None  # type: ignore

def test_api(provider: str, endpoint: str, api_key: str, aws_access_key_id: str = None, aws_secret_access_key: str = None) -> Tuple[bool, str]:
	try:
		hdrs: Dict[str, str] = {}
		url = endpoint
		name = provider.lower()
		if name.startswith("openai"):
			url = endpoint.rstrip("/") + "/models"
			hdrs["Authorization"] = f"Bearer {api_key}"
		elif name.startswith("anthropic"):
			url = endpoint.rstrip("/") + "/models"
			hdrs["x-api-key"] = api_key
		elif "azure" in name and "openai" in name:
			if "{" in endpoint or "}" in endpoint:
				return False, "Replace placeholders in endpoint (e.g., {resource})"
			url = endpoint.rstrip("/") + "/openai/deployments?api-version=2023-05-15"
			hdrs["api-key"] = api_key
		elif name.startswith("google") or "gemini" in name:
			url = endpoint.rstrip("/") + "/models"
			hdrs["x-goog-api-key"] = api_key
		elif name.startswith("mistral"):
			url = endpoint.rstrip("/") + "/models"
			hdrs["Authorization"] = f"Bearer {api_key}"
		elif name.startswith("cohere"):
			url = endpoint.rstrip("/") + "/models"
			hdrs["Authorization"] = f"Bearer {api_key}"
		elif name.startswith("groq"):
			url = endpoint.rstrip("/") + "/models"
			hdrs["Authorization"] = f"Bearer {api_key}"
		elif name.startswith("openrouter"):
			url = endpoint.rstrip("/") + "/models"
			hdrs["Authorization"] = f"Bearer {api_key}"
		elif "ollama" in name:
			url = endpoint.rstrip("/") + "/api/tags"
		elif "bedrock" in name:
			try:
				import os
				import boto3  # type: ignore
				from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
			except Exception:
				return False, "Install boto3 to test Bedrock (pip install boto3)"

			region = (endpoint or "").strip() or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
			if not region:
				return False, "Provide AWS region in Endpoint or set AWS_REGION/AWS_DEFAULT_REGION"
			try:
				session_kwargs = {"region_name": region}
				ak = (aws_access_key_id or "").strip() if aws_access_key_id else ""
				sk = (aws_secret_access_key or "").strip() if aws_secret_access_key else ""
				if ak and sk:
					session = boto3.Session(aws_access_key_id=ak, aws_secret_access_key=sk, region_name=region)
					client = session.client("bedrock")
				else:
					client = boto3.client("bedrock", **session_kwargs)
				resp = client.list_foundation_models()
				summaries = resp.get("modelSummaries", [])
				return True, f"Bedrock reachable in {region} ({len(summaries)} models)"
			except ClientError as e:  # type: ignore
				try:
					msg = e.response.get("Error", {}).get("Message", str(e))
				except Exception:
					msg = str(e)
				return False, f"AWS ClientError: {msg}"
			except BotoCoreError as e:  # type: ignore
				return False, f"AWS BotoCoreError: {str(e)}"
			except Exception as e:
				return False, str(e)

		if requests is None:
			return False, "Install requests library (pip install requests)"
		
		# Validate URL scheme for security
		if not url.startswith(('http://', 'https://')):
			return False, "Invalid URL scheme. Only HTTP/HTTPS allowed."
		
		resp = requests.get(url, headers=hdrs, timeout=10)
		if 200 <= resp.status_code < 300:
			return True, f"API reachable (HTTP {resp.status_code})"
		return False, f"HTTP {resp.status_code}"
	except requests.exceptions.HTTPError as e:
		return False, f"HTTP Error: {str(e)}"
	except requests.exceptions.RequestException as e:
		return False, f"Request Error: {str(e)}"
	except Exception as e:
		return False, str(e)