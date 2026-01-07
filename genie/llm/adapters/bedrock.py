from typing import Any, Dict, Optional
import logging

try:
	import boto3
	from langchain_aws import ChatBedrockConverse
except Exception:
	boto3 = None  
	ChatBedrockConverse = None
# try:
#     import sys
#     print(f"sys.path: {sys.path}", flush=True)
#     print(f"Attempting boto3 import...", flush=True)
#     import boto3
#     print(f"boto3 imported: {boto3}", flush=True)
#     print(f"Attempting langchain_aws import...", flush=True)
#     from langchain_aws.chat_models.bedrock_converse import ChatBedrockConverse 
#     print(f"ChatBedrockConverse imported: {ChatBedrockConverse}", flush=True)
# except Exception as e:
#     print(f"Import failed: {e}", flush=True)
#     import traceback
#     traceback.print_exc()
#     boto3 = None  
#     ChatBedrockConverse = None

logger = logging.getLogger('genie.llm.adapters.bedrock')  


def build(cfg: Dict[str, Any], model: Optional[str] = None):
	logger.info(f"Building AWS Bedrock LLM with model: {model}")
	logger.info(f"boto3: {boto3}")
	logger.info(f"ChatBedrockConverse: {ChatBedrockConverse}")
	if boto3 is None or ChatBedrockConverse is None:
		logger.error("AWS dependencies not available")
		raise ImportError("Bedrock adapter requires boto3 and langchain_aws.")
	
	model = model or (cfg.get("model") or "").strip() or None
	region = (cfg.get("base_url") or cfg.get("endpoint") or "").strip() or None
	
	logger.debug(f"Bedrock config - model: {model}, region: {region}")
	
	if not model:
		logger.error("Model not specified for Bedrock")
		raise ValueError("Model is required for AWS Bedrock")
	if not region:
		logger.error("Region not specified for Bedrock")
		raise ValueError("Region is required for AWS Bedrock")
	
	ak = (cfg.get("aws_access_key_id") or "").strip()
	sk = (cfg.get("aws_secret_access_key") or "").strip()
	logger.debug(f"AWS credentials - access_key: {'***' if ak else 'None'}, secret_key: {'***' if sk else 'None'}")
	
	session = boto3.Session(aws_access_key_id=ak, aws_secret_access_key=sk, region_name=region)
	runtime = session.client("bedrock-runtime")
	logger.info(f"Successfully created Bedrock ChatLLM instance for model {model} in region {region}")
	return ChatBedrockConverse(model_id=model, client=runtime)


























