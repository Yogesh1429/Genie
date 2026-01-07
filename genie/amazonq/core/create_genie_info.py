import logging
import time
import sys
import wexpect
import os

logger = logging.getLogger(__name__)
def create_genie_file(child : wexpect.spawn):	
	content = '''Here's the GenIE_json schema. Use it When I say in the prompt to use, as I will be passing the response to another app:

**JSON Response Schema:**

GenIE_json
{
	"response": "string - The main response content to the user's request, Do not include raw line breaks inside.",
	"tool_use": "string|null - Name of the tool that you want to use, or null if no tool needs to be used",
	"approval_required": "boolean- True if user approval is needed before proceeding with tool actions, False otherwise",
	"approval_prompt": "string|null - Specific question/request for user approval, or null if no approval needed"
}                            

**Special Instructions:**
- start the response with GenIE_json  
- Always format responses as valid json with the above structure for this session
- Include the main response content in the 'response' field 
- Replace all raw line breaks with '\\n'. 
- If you want to ask - "Allow this action? Use 't' to trust (always allow) this tool for the session. [y/n/t]" then Set 
it as approval string in 'approval_prompt' and approval_required to true, Set 'tool_use' to name of the tool that you intent to use, or null if none
- Set both 'tool_use' and 'approval_prompt' to null when no tools are required
- Ensure json is properly escaped and formatted
- when showing code block in JSON responses, wrap with triple dollar signs ($$$\n) before and after the code.
- once your response is ready, verify the response is in given json schema
- User can understand the response in GenIE_json format only

Please ensure your GenIE_json response is Windows-compatible by following these rules:
- Never include literal newline characters inside JSON string values
- Always escape newlines as \\n within strings (not actual line breaks)
- Use only standard ASCII characters - no Unicode control characters or smart quotes
- Ensure all string content is properly escaped according to GenIE_json specification
- validate the GenIE_json
'''

	filepath = f"$HOME/info.txt"
	# ✅ DISABLE TERMINAL BELL
	child.sendline("bind 'set bell-style none' 2>/dev/null && echo 'Bell disabled' || echo 'Bell disable failed'")
	time.sleep(0.1)
	child.sendline(f"cat > {filepath} <<EOF")
	for line in content.splitlines():
		child.sendline(line)
	child.sendline("EOF")

	logger.info("GenIE Info File created successfully.")
	return