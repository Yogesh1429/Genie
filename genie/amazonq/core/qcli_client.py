import asyncio
import logging
import os
import re
import sys
import time
import wexpect
from typing import Optional, Any

from .create_genie_info import create_genie_file
from ..utils.qcli_keyboard import QCLIKeyboard
from ...config_loader import get_chat_history_path, get_qcli_default_model
from ..utils.convert import windows_to_wsl_path
from ...config_loader import get_identity_provider, get_region
from .json_processor import JSONProcessor
logger = logging.getLogger(__name__)

class QCLIClient:
    def __init__(self, json_processor: JSONProcessor):
        self.json_processor = json_processor
        self.child: Optional[Any] = None
        self.init_error = None
        self.init_lock = asyncio.Lock()
        # keyboard helper
        self.keyboard = None
        self.chat_history_path = get_chat_history_path()
        self.chat_history_path = windows_to_wsl_path(self.chat_history_path)
        logger.info(f"Chat history path: {self.chat_history_path}")
        self.auth_url = None
    
    def clear_buffer(self, flush_timeout=5, max_empty_reads=5):
        """Flush any pending output from the child process buffer.
        
        Args:
            flush_timeout: The maximum time to wait for the buffer to clear.
            max_empty_reads: Number of consecutive empty reads before considering buffer clear
        """
        empty_read_count = 0
        end_time = time.time() + flush_timeout
        flushed = ""
        logger.info("Inside clear buffer")
        while True:
            try:
                chunk = self.child.read_nonblocking(size=1024)
                if chunk:
                    flushed += chunk
                    logger.info(f"[FLUSHED] {len(chunk)} {chunk}")
                    empty_read_count = 0
                else:
                    empty_read_count += 1
                    if empty_read_count >= max_empty_reads:
                        logger.info(f"Max empty reads {max_empty_reads} reached, stopping buffer flush")
                        break
                    if time.time() > end_time:
                        break
                    time.sleep(0.05)
            except (wexpect.TIMEOUT, wexpect.EOF):
                logger.info("Timeout waiting for buffer to clear")
                break
            except UnicodeDecodeError:
                pass
            except Exception as e:
                logger.info(f"❌ Failed to clear buffer: {e}")
                break
    
    async def send_and_wait_for_qcli(self, message: str, timeout, clear_buffer=True) -> str:
        if clear_buffer:
            self.clear_buffer()
        self.child.sendline(message)
        logger.info(f"Query sent: {message}")
        buffer = ""
        start_time = time.time()
        last_data_time = time.time()
        silence_threshold = 5.0
        overall_timeout = timeout
        EOM = DATA_RECEIVED = False
        
        # if message.__eq__ ('/quit'):
        #     self.close()
        #     logger.info("Q CLI Closed")
        #     return "Q CLI Closed"
			
        while True:
            if time.time() - start_time > overall_timeout:
                # logger.warning(f"Overall timeout reached : {overall_timeout}s")
                if buffer == '':
                    buffer = (f"Overall timeout reached : {overall_timeout}s")
                logger.info(f"buffer--> {buffer}, Timeout reached: {timeout}s")
                break
            try:
                chunk = self.child.read_nonblocking(size=1024)
                if EOM and chunk == '':
                    if time.time() - last_data_time > silence_threshold:
                        logger.info(f"EOM detected and silence threshold {silence_threshold}s. Good to go!")
                        break
                    else:
                        continue
                
                if chunk:
                    start_time = time.time()
                    EOM = False
                    last_data_time = time.time()
                    if chunk.endswith("Thinking...") and len(chunk) == 14:
                        continue
                    if chunk.endswith("> "):
                        EOM = True
                        # DEEPA
                        logger.info(f"EOM detected --> {chunk}")
                    # if chunk.endswith("GenIE_end_json"):
                    #     EOM = True
                    #     break
                    # DEEPA
                    buffer += chunk
                    DATA_RECEIVED = True
                
                if (not DATA_RECEIVED) and (time.time() - start_time > timeout):
                    logger.info(f"No data received and timed-out after {timeout}s")
                    buffer = (f"No data received and timed-out after {timeout}s")
                    break
            except UnicodeDecodeError as e:
                # logger.info(f"Unicode decode error: {e}")
                pass
            except Exception as e:
                logger.info(f"❌ Failed send: {e}")
                break

        if buffer == '':
            buffer = ("No data received and timed-out")

        return buffer

    async def __launch_qcli_with_model(self, model_name: str):
        self.clear_buffer()
        self.child.sendline(f"Kiro-cli chat --model {model_name}")
        # self.child.sendline(f"q chat --model {model_name} --resume")
        try:
            matched = self.child.expect([r'>'], timeout=80)
            logger.info(f"✅ Kiro-cli chat prompt detected (type: {matched})")

        except wexpect.TIMEOUT:
            logger.error("❌ Timeout waiting for Kiro-cli chat prompt")
            raise

    # async def initialize(self) -> None:
    #     """Initialize the Q CLI connection"""
    #     async with self.init_lock:
    #         if self.child is None:
    #             real_executable = sys.executable
    #             try:
    #                 if sys._MEIPASS is not None:
    #                     sys.executable = os.path.join(sys._MEIPASS, "wexpect", "wexpect.exe")
    #             except AttributeError:
    #                 pass
                
    #             logger.info("💬 Launching WSL...")
    #             self.child = wexpect.spawn('wsl', encoding='utf-8', errors='replace')
    #             logger.info(f"✅ WSL spawned: alive={self.child.isalive()}")  
    #             sys.executable = real_executable                
                
    #             #This is for the userlogin process
    #             QCLI_USER_NAME = os.getenv("QCLI_USER_NAME")
    #             if QCLI_USER_NAME is None:
    #                 QCLI_USER_NAME = "deepa"

    #             logger.info(f"👤 User: {QCLI_USER_NAME}")
    #             self.child.sendline(f"sudo su - {QCLI_USER_NAME}")
    #             self.child.expect([r'\$', r'>', r'#'], timeout=15)
    #             logger.info("✅ Bash prompt detected")
    #             try:
    #                 matched = self.child.expect([r'\$', r'>', r'#'], timeout=15)
    #                 logger.info(f"✅ Bash prompt detected (type: {matched})")
    #             except wexpect.TIMEOUT:
    #                 logger.error("❌ Timeout waiting for bash prompt")
    #                 raise			
    #             # ------------------------------------------------

    #             # create_genie_file(self.child) --> Not needed s it is in package working directory
    #             # self.child.sendline("q login --license pro --identity-provider https://d-906623ee99.awsapps.com/start --region us-east-1")
    #             self.child.sendline("q login --license pro")
    #             time.sleep(1)
    #             # response = await self.send_and_wait_for_qcli("q login --license pro --identity-provider https://d-906623ee99.awsapps.com/start --region us-east-1",timeout=30)   # run q login
    #             # time.sleep(1)

    #             # Wait for the menu to appear
    #             response = self.child.expect("Enter Start URL")
    #             logger.info(f"response: {response}")
    #             self.child.send("\r") 
    #             time.sleep(0.5)
    #             response = self.child.expect("Enter Region")
    #             logger.info(f"response: {response}")
    #             self.child.send("\r")  
    #             time.sleep(0.5)
    #             response = self.child.expect([r'Logging in..'], timeout=3)
    #             logger.info(f"response: {response}")
    #             logger.info("------")
    #             response = self.child.before
    #             logger.info(f"before response--> \n: {response}")
    #             import re
    #             url_match = re.search(r'Open this URL:\s*(https?://\S+)', response)
    #             if url_match:
    #                 auth_url = url_match.group(1)
    #                 logger.info(f"Authentication URL: {auth_url}")
    #                 self.auth_url = auth_url
    #             else:
    #                 logger.warning("Authentication URL not found")
    #             logger.info("------")

    #             return 
    
    async def initialize(self) -> None:
        """Initialize the Q CLI connection"""
        async with self.init_lock:
            if self.child is None:
                real_executable = sys.executable
                try:
                    if sys._MEIPASS is not None:
                        sys.executable = os.path.join(sys._MEIPASS, "wexpect", "wexpect.exe")
                except AttributeError:
                    pass
                
                #This is for the userlogin process
                QCLI_USER_NAME = os.getenv("QCLI_USER_NAME")

                logger.info("💬 Launching WSL...")
                self.child = wexpect.spawn(f'wsl -u {QCLI_USER_NAME}', encoding='utf-8', errors='replace')
                logger.info(f"✅ WSL spawned: alive={self.child.isalive()}")  
                sys.executable = real_executable                
                
                
                #This is for the userlogin process
                # QCLI_USER_NAME = os.getenv("QCLI_USER_NAME")
                # if QCLI_USER_NAME is None:
                #     QCLI_USER_NAME = "deepa"

                logger.info(f"👤 User: {QCLI_USER_NAME}")
                # self.child.sendline(f"sudo su - {QCLI_USER_NAME}")
                # self.child.expect([r'\$', r'>', r'#'], timeout=15)
                # logger.info("✅ Bash prompt detected")
                try:
                    matched = self.child.expect([r'\$', r'>', r'#'], timeout=30)
                    logger.info(f"✅ Bash prompt detected (type: {matched})")
                except wexpect.TIMEOUT:
                    logger.error("❌ Timeout waiting for bash prompt")
                    raise			
                # ------------------------------------------------

                # create_genie_file(self.child) --> Not needed s it is in package working directory
                # self.child.sendline("q login --license pro --identity-provider https://d-906623ee99.awsapps.com/start --region us-east-1")
                # self.child.sendline("q login --license pro")
                identity = get_identity_provider()
                region = get_region()
                logger.info(f"identity: {identity}")
                logger.info(f"region: {region}")
                self.child.sendline(f"kiro-cli login --license pro --identity-provider {identity} --region {region}")
                time.sleep(1)
                # response = await self.send_and_wait_for_qcli("q login --license pro --identity-provider https://d-906623ee99.awsapps.com/start --region us-east-1",timeout=30)   # run q login
                # time.sleep(1)

                # Wait for the menu to appear
                response = self.child.expect(["Enter Start URL", "error: Already logged in, please logout with q logout first", "error: Already logged in, please logout with kiro-cli logout first"], timeout=15)
                if response == 1 or response == 2:
                    logger.warning("Already logged in.")
                    self.auth_url = "Already logged in"
                    return

                logger.info(f"response: {response}")
                self.child.send("\r") 
                time.sleep(0.5)
                response = self.child.expect("Enter Region")
                logger.info(f"response: {response}")
                self.child.send("\r")  
                time.sleep(0.5)
                response = self.child.expect([r'Logging in..'], timeout=3)
                logger.info(f"response: {response}")
                logger.info("------")
                response = self.child.before
                logger.info(f"before response--> \n: {response}")
                
                url_match = re.search(r'Open this URL:\s*(https?://\S+)', response)
                if url_match:
                    auth_url = url_match.group(1)
                    logger.info(f"Authentication URL: {auth_url}")
                    self.auth_url = auth_url
                else:
                    logger.warning("Authentication URL not found")
                logger.info("------")

                return 

    async def launch_q_chat(self):    
        logger.info("💬 Launching Kiro-cli chat...")
        self.child.sendline("\r")
        # self.child.sendline("q chat --model claude-sonnet-4")
        default_model = get_qcli_default_model()
        logger.info(f"Default Model: {default_model}")
        self.child.sendline(f"kiro-cli chat --model {default_model}")
        # self.child.expect([r'\$', r'>'], timeout=30)
        try:
            matched = self.child.expect([r'>'], timeout=60)
            logger.info(f"✅ Kiro-cli chat prompt detected (type: {matched})")
        except wexpect.TIMEOUT:
            logger.error("❌ Timeout waiting for Kiro-cli chat prompt")
            raise
        
        # Send initial schema setup
        # question = f'Hello!'
        # response = await self.send_and_wait_for_qcli(f"{question}", timeout=30)
        # time.sleep(4)
        
        # question = f'I am {QCLI_USER_NAME}.'
        # response = await self.send_and_wait_for_qcli(f"{question}", timeout=30)
        # logger.info(f"response: {response}")

    # commented below code to check if /context works
        # question = "Please read genie_info.txt in the working directory for instructions/rules."
        # response = await self.send_and_wait_for_qcli((f"*~{question}~*"), timeout=40, clear_buffer = False)
        # logger.info(f"response: {response}")
                

        # filtered_response = response.rsplit(f"~*", 1)[1] if f"~*" in response else None
        # logger.info(f"response: {filtered_response}")

        

        response = await self.ask_question("/context add genie_info.txt", timeout=5)
        logger.info(f"response: {response}")
        clean_response = self.json_processor.process_response("/context add genie_info.txt", response)
        logger.info(f"clean_response: {clean_response}")

        # response = await self.ask_question("/tools trust search_knowledge_base", timeout=5)
        # logger.info(f"response: {response}")
        # clean_response = self.json_processor.process_response("/context add genie_info.txt", response)
        # logger.info(f"clean_response: {clean_response}")


        self.keyboard = QCLIKeyboard(self.child)
        logger.info("🤖 Kiro-cli chat ready.")
    
    async def ask_question(self, user_input: str, timeout=10) -> str:
        """Send question to Q CLI and get response"""
        logger.info(f"timeout: {timeout}")
        user_input = user_input.strip()
        if user_input.startswith('/') or user_input.startswith('@') or user_input in ['t', 'y', 'n']:
            response = await self.send_and_wait_for_qcli(user_input, clear_buffer = True, timeout = timeout)
            # if user_input == '/model' :
            #     self.keyboard.send_escape()
            #     time.sleep(1)
        else:
            response = await self.send_and_wait_for_qcli(
                f"*~{user_input}~*. Use the given special instructions to respond in the provided json Response schema.",
                timeout = timeout
            )
        return response
    
    async def update_model(self, model_name: str):
        """Update the model for the Q CLI"""
        response = await self.ask_question('/model', timeout=10)
        logger.info(f"model change response: {response}")
        time.sleep(1)
        clean_response = self.json_processor.process_and_extract_json('/model', response)
        models = []
       
        models = re.findall(r'claude-[^\s]+', clean_response)
        logger.info(f"Found models: {models}")
        target_position = 0
        model_found = False
        for i, model in enumerate(models):
            if model_name == model:
                target_position = i
                model_found = True
                break
 
        if model_found:
            self.keyboard.send_down(target_position)
            self.keyboard.send_enter()
            time.sleep(0.5)
            return 'model updated successfully'
        else:
            logger.warning(f"Model '{model_name}' not found in available models: {models}")
            return f'Model {model_name} not found'
            
    # async def update_model(self, model_name: str):
    #     # response = await self.ask_question('/model', timeout=2)
    #     # time.sleep(2)
    #     # logger.info(f"{response}")
    #     # self.keyboard.send_down(2)
    #     # self.keyboard.send_enter()

    #     response = await self.ask_question('/model', timeout=10)
    #     response = self.json_processor.process_response('/model', response)
    #     logger.info(f"response  1: {response}")
    #     match = "Select a model for this chat session"
    #     response = response.split(match, 1)[1]  
    #     logger.info(f"response  2: {response}")
    #     response = response.split('❯',1)[1].strip() if '❯' in response else None
    #     logger.info(f"response  3: {response}")
    #     model_name1 = model_name + ' '
    #     logger.info(f"model_name1: {model_name1}.")
    #     if model_name in response:
    #         response = response.split(model_name1,1)[0].strip() 
    #         count = response.count('claude')
    #         logger.info(f"response  4: {response}")
    #         logger.info(f"count: {count}")
    #         if count == 3: # claude-3-5-sonnet is the 3rd option in the list there is no space at the end.
    #             count = 2
    #         if count > 0:
    #             logger.info(f"sending down {count} times")
    #             self.keyboard.send_down(count) 
    #         elif count < 0:
    #             logger.warning(f"Model {model_name} not found in the list")
    #             return f"Model {model_name} not found in the list"
    #         self.keyboard.send_enter()
    #     logger.info(f"model updated successfully: {response}")


    #     """Update the model for the Q CLI"""
    #     # file_name = f"{self.chat_history_path}/_temp_conv_qcli.json"
    #     # response = await self.ask_question(f'/save -f {file_name}', timeout=2)
    #     # time.sleep(2)
    #     # logger.info(f"{response}")
    #     # self.child.sendline("/quit")
    #     # time.sleep(1)
    #     # response = await self.__launch_qcli_with_model(model_name)
    #     # response = await self.ask_question(f'/load {file_name}', timeout=2)
    #     # logger.info(f"{response}")
    #     # self.child.sendline("/quit")
    #     # time.sleep(1)
    #     # response = await self.__launch_qcli_with_model(model_name)
    #     # logger.info(f"model updated successfully: {response}")

    #     # self.keyboard.navigate_menu(steps_down=model_number)
    #     # self.keyboard.send_enter()
    #     # response = await self.ask_question('/model', timeout=3)
    #     # logger.info(f"model change response: {response}")
    #     # self.keyboard.send_escape()
    #     # self.keyboard.select_option(2)
    #     # response = await self.send_and_wait_for_qcli(f"q model {profile_name} {model_name}", timeout=30)
    #     # logger.info(f"response: {response}")
    #     return 'model updated successfully'
		
    async def save_memory(self, file_name: str):
        """Save the conversation memory to a JSON file"""
        logger.info(f"Saving memory to {file_name}")
        # file_name = f"{self.chat_history_path}/{file_name}"
        file_name = windows_to_wsl_path(file_name)
        logger.info(f"Saving memory to {file_name}")
        # self.child.sendline(f"/save -f {file_name}")
        response = await self.ask_question(f'/save -f "{file_name}"', timeout=10)
        logger.info(f"response: {response}")
        # time.sleep(2)
        response = "Memory saved successfully"
        logger.info(f"Memory saved successfully: {response}")
        return response
    
    def load_memory(self, file_name: str):
        """Load the conversation memory from a JSON file"""
        logger.info(f"Loading memory from {file_name}")
        # file_name = f"{self.chat_history_path}/{file_name}"
        file_name = windows_to_wsl_path(file_name)
        logger.info(f"Loading memory from {file_name}")
        self.child.sendline(f'/load "{file_name}"')
        # time.sleep(2)
        response = "Memory loaded successfully"
        logger.info(f"Memory loaded successfully: {response}")
        return response
    
    # def close(self):
    #     """Close the Q CLI connection"""
    #     if not self.child:
    #         return
        
    #     try:
    #         if self.child.isalive():
    #             try:
    #                 self.child.sendline("/quit")
    #                 time.sleep(1)
    #                 # self.child.sendline("q logout")
    #                 logger.info("Closing Q CLI connection")
    #             except Exception:
    #                 pass
    #         try:
    #             self.child.close(force=True)
    #             logger.info("wsl closed")
    #         except Exception:
    #             pass
    #     finally:
    #         self.child = None
    def close(self):
        """Close the Kiro CLI connection cleanly (and avoid WinError 6 logs)."""
        child = getattr(self, "child", None)
        if not child:
            return

        try:
            if child.isalive():
                # 1) Try graceful exits
                try:
                    self.child.sendline("/quit")
                    time.sleep(1)
                    # self.child.sendline("q logout")
                    logger.info("Kiro CLI exited, closing WSL connection")
                except Exception:
                    pass

            # 3) If still alive, terminate (don’t use close(force=True) first)
            if child.isalive():
                try:
                    child.terminate(force=True)  # tell wexpect we terminated it
                except Exception:
                    pass

            # 4) Always call close() WITHOUT force so wexpect marks it as closed
            try:
                child.close()  # no 'force' → sets internal flags so __del__ is a no-op
            except Exception:
                pass

        finally:
            self.child = None

    async def clear_memory(self):
        """Clear the conversation memory"""
        logger.info("Clearing memory")
        response = await self.ask_question("/clear", timeout=3)
        clean_response = self.json_processor.process_response("/clear", response)
        logger.info(f"clean_response: {clean_response}")
        time.sleep(1)
        if "y/n" in clean_response:
            response = await self.ask_question("y", timeout=3)
            logger.info(f"response: {response}")
            clean_response = self.json_processor.process_response("y", response)
            logger.info(f"clean_response: {response}")
            return "Memory cleared successfully"
            # if  "Conversation history cleared" in response:
            #     response = await self.ask_question("/context add genie_info.txt", timeout=5)
            #     logger.info(f"response: {response}")
            #     clean_response = self.json_processor.process_response("/context add genie_info.txt", response)
            #     logger.info(f"clean_response: {clean_response}")
                # response = await self.ask_question("@genie")
                # logger.info(f"response: {response}")
                # question = "Please read genie_info.txt in the working directory for instructions/rules."
                # logger.info(f"{question} sent to Q CLI")
                # response = await self.send_and_wait_for_qcli((f"*~{question}~*"), timeout=40, clear_buffer = False)
                # filtered_response = self.json_processor.process_response(question, response)
                # logger.info(f"response: {filtered_response}")

                # # filtered_response = response.rsplit(f"~*", 1)[1] if f"~*" in response else None
                # # logger.info(f"response: {filtered_response}")
                # return "Memory cleared successfully"
            
        return "Memory not cleared"

    def process_response_json(self, request: str, response: str) -> str:
        """Process the response from the Kiro CLI"""
        clean_response = self.json_processor.process_and_extract_json(request, response)
        logger.info(f"Result: {clean_response}")
        return clean_response