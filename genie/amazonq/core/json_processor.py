import logging
import re
from typing import Optional
from ..utils.json_extracter import extract_with_packages, convert_json

logger = logging.getLogger(__name__)
class JSONProcessor:
    def __init__(self):
        self.ansi_pattern = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
    
    def strip_ansi_only(self, text: str) -> str:
        """Remove ANSI escape codes from text"""
        return self.ansi_pattern.sub('', text)
    
    def process_response(self, user_input: str, response: str) -> Optional[str]:
        """Extract relevant response based on user input"""
        filtered_response = None
        if user_input.startswith('/'):
            filtered_response = response.rsplit(f"{user_input}", 1)[1] if f"{user_input}" in response else None
        elif user_input in ['t', 'y', 'n']:
            filtered_response = response.rsplit(f"> {user_input}", 1)[1] if f"> {user_input}" in response else None
        else:
            input_first_line = user_input.split('\\n')[0]
            # input_first_line = user_input.split('\n')[0]
            logger.debug(f"Input first line: {input_first_line}")			
            filtered_response = response.rsplit(f"*~{input_first_line}", 1)[1] if f"*~{input_first_line}" in response else None
        logger.debug(f"Filtered response: {filtered_response}")
        return filtered_response
    
    def process_and_extract_json(self, user_input: str, response: str) -> str:
        """Process response and extract JSON"""
        logger.info(f"Processing response: {response}")
        filtered_response = self.process_response(user_input, response)
        
        if filtered_response is not None:
            filtered_response = self.strip_ansi_only(filtered_response)
            filtered_response = filtered_response.replace("\\r\\n", "\\n")
            # filtered_response = filtered_response.replace("\r\n", "\n")
        
        if filtered_response is None:
            # filtered_response = response.rsplit("GenIE_json", 1)[1]
            # logger.info(f"Filtered response: {filtered_response}")
            # return extract_with_packages("GenIE_json" + filtered_response)
            return "No response from Kiro CLI"
        # DEEPA !!!! json issue !!! The first characters of the response MUST be exactly:
        # GenIE_json{
        # Also, I added this check
        if "> json" in filtered_response:
            filtered_response.replace("> json", "GenIE_json")

        if "GenIE_json" not in filtered_response:
            if "~*. Use the given special instructions to respond in the provided json Response schema." in filtered_response:
                filtered_response = filtered_response.rsplit("~*. Use the given special instructions to respond in the provided json Response schema.", 1)[1]
            filtered_response = convert_json(filtered_response)
            filtered_response = "GenIE_json" + filtered_response
        
        if "GenIE_json" in filtered_response:
            filtered_response = extract_with_packages(filtered_response)
        
        return filtered_response