#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import argparse
import sys
import signal
import re
import logging
from autoagents.roles import Manager, ObserverAgents, ObserverPlans
from autoagents.explorer import Explorer
import startup
import ws_service

logging.basicConfig(level=logging.WARNING, format='%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

def signal_handler(signal, frame):
    sys.exit(1)

async def commanline(investment: float = 10.0, n_round: int = 3, proxy: str = None, llm_api_key: str = None, serpapi_key: str=None, idea: str=None):
    if llm_api_key is None:
        print("OpenAI API key:")
        llm_api_key = input().strip()
    if serpapi_key is None:
        print("SerpAPI key:")
        serpapi_key = input().strip()
    if idea is None:
        print("Give me a task idea:")
        idea = input().strip()
    await startup.startup(idea, investment, n_round, llm_api_key=llm_api_key, serpapi_key=serpapi_key, proxy=proxy)

async def service(host: str = "localhost", port: int = 9000, proxy: str=None, llm_api_key: str=None, serpapi_key: str=None):
    await ws_service.run_service(host=host, port=port, proxy=proxy, llm_api_key=llm_api_key, serpapi_key=serpapi_key)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description="AutoAgents")
    ### TODO: set mode default to commandline
    parser.add_argument("--mode", default="commandline", choices=["commandline", "service"], help="mode=commandline, service")
    parser.add_argument("--host", default="127.0.0.1", help="websocket backend service host")
    parser.add_argument("--port", default=9000, type=int, help="websocket backend service port")
    parser.add_argument("--proxy", default=None, type=str, help="http proxy, example: http://127.0.0.1:8080")
    parser.add_argument("--llm_api_key", default=None, type=str, help="OpenAI API key")
    parser.add_argument("--serpapi_key", default=None, type=str, help="SerpAPI key")
    parser.add_argument("--idea", default=None, type=str, help="Give me a task idea")
    args = parser.parse_args()

    proxy = None
    proxy_regex = r'(http|https|socks|socks5):\/\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}'
    if args.proxy and re.match(proxy_regex, args.proxy):
        proxy = args.proxy

    if args.mode == "commandline":
        asyncio.run(commanline(proxy=proxy, llm_api_key=args.llm_api_key, serpapi_key=args.serpapi_key, idea=args.idea))
    elif args.mode == "service":
        asyncio.run(service(host=args.host, port=args.port, proxy=proxy, llm_api_key=args.llm_api_key, serpapi_key=args.serpapi_key))
    else:
        logger.error(f"Invalid mode: {args.mode}")