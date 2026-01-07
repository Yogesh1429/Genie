from typing import Any, Dict, Optional
import logging

try:
    from langchain_ibm import ChatWatsonx
except ImportError:
    ChatWatsonx = None

logger = logging.getLogger('genie.llm.adapters.watsonx')


def build(cfg: Dict[str, Any], model: Optional[str] = None):
    logger.info(f"Building IBM Watson LLM with model: {model}")
    
    if ChatWatsonx is None:
        logger.error("langchain_ibm not available")
        raise ImportError("IBM Watson adapter requires 'langchain-ibm' package.")
    
    # Extract configuration
    model = model or (cfg.get("model") or "").strip() or None
    api_key = (cfg.get("api_key") or "").strip() or None
    url = (cfg.get("base_url") or cfg.get("endpoint") or "").strip() or None
    project_id = (cfg.get("project_id") or "").strip() or None
    space_id = (cfg.get("space_id") or "").strip() or None
    
    logger.debug(f"Watson config - model: {model}, url: {url}, api_key: {'***' if api_key else 'None'}")
    
    # Validate required parameters
    if not api_key:
        logger.error("IBM Watson API key is missing")
        raise ValueError("IBM Watson api_key is required (store in profile or set WATSONX_APIKEY).")
    
    if not url:
        logger.error("IBM Watson URL is missing")
        raise ValueError("IBM Watson url is required.")
    
    if not model:
        logger.error("Model not specified for IBM Watson")
        raise ValueError("Model is required for IBM Watson")
    
    # At least one of project_id or space_id is required
    if not project_id and not space_id:
        logger.error("Neither project_id nor space_id provided")
        raise ValueError("Either project_id or space_id is required for IBM Watson")
    
    # Build kwargs for ChatWatsonx
    kwargs: Dict[str, Any] = {
        "model_id": model,
        "url": url,
        "apikey": api_key,
    }
    
    if project_id:
        kwargs["project_id"] = project_id
    elif space_id:
        kwargs["space_id"] = space_id
    
    # Optional parameters
    params = cfg.get("params", {})
    if params:
        kwargs["params"] = params
    
    logger.info(f"Successfully created IBM Watson ChatLLM instance for model {model}")
    return ChatWatsonx(**kwargs)

if __name__ == "__main__":
    # Test configuration
    test_cfg = {
        "api_key": "CoVP83lHvmJkMVC3U5UJrKNw1Z8OhnQLMMEJb7qXMA-W",
        "base_url": "https://us-south.ml.cloud.ibm.com",
        "project_id": "35159d68-d67a-4ae0-9907-6febf4ea996b",  # or use "space_id" instead
        # "model": "ibm/granite-13b-chat-v2",
        "model": "ibm/granite-3-3-8b-instruct",
        "params": {
            "temperature": 0.7,
            "max_tokens": 200
        }
    }
    
    try:
        # Build the LLM
        llm = build(test_cfg)
        print(f"✓ Successfully created Watson LLM: {llm}")
        
        # Test a simple invocation
        response = llm.invoke("Hello! What is 2+2?")
        print(f"\n✓ Response: {response.content}")
        
    except ImportError as e:
        print(f"✗ Import Error: {e}")
        print("Install: pip install langchain-ibm")
    except ValueError as e:
        print(f"✗ Configuration Error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()