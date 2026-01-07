#!/usr/bin/env python3
import tkinter as tk
from genie.llm.ui.selector import LLMProviderSelector
from genie.log_setup import setup_logging
import logging
import argparse
from genie.config_loader import load_config, get_log_level, get_log_path, get_providers_file, get_log_retention_days
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM Provider Selector Launcher")
    parser.add_argument("--config", type=str, help="Config file")
    parser.add_argument("--providers-file", type=str, help="Providers file")
    parser.add_argument("--log-path", type=str, dest="log_path", help="Log file location")
    args = parser.parse_args()
    # Setup logging for the entire application
    print(f"args: {args}")    
    cfg = load_config(args.config)
    print(f"cfg: {cfg}")
    log_level = get_log_level(cfg)
    print(f"log_level: {log_level}")
    log_path = args.log_path
    if not log_path:
        log_path = get_log_path(cfg)
    log_days = get_log_retention_days(cfg)
    print(f"log_days: {log_days}")
    print(f"log_path: {log_path}")
    print(f"providers_file: {args.providers_file}")
    setup_logging(log_level=log_level, log_dir=log_path, log_retention_days=log_days)
    logger = logging.getLogger('genie.LLMProviderSelector')
    logger.info("Starting LLM Provider Selector GUI")

    # providers_file = get_providers_file(cfg)
    providers_file = args.providers_file
    if providers_file:
        os.environ["APP_PROVIDERS_FILE"] = providers_file

    root = tk.Tk()
    app = LLMProviderSelector(root)
    logger.info("LLM Provider Selector GUI started")
    root.mainloop()
    
    logger.info("LLM Provider Selector GUI closed")