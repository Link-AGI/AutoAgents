from datetime import datetime
import websockets
import asyncio
import os
import uuid
import json
import functools
import traceback
import sys
import logging
from multiprocessing import current_process, Process, Queue, queues

from common import MessageType, format_message, timestamp
import startup
user_dict = {}

KEY_TO_USE_DEFAULT = os.getenv("KEY_TO_USE_DEFAULT")
DEFAULT_LLM_API_KEY = os.getenv("DEFAULT_LLM_API_KEY") if KEY_TO_USE_DEFAULT is not None else None
DEFAULT_SERP_API_KEY = os.getenv("DEFAULT_SERP_API_KEY") if KEY_TO_USE_DEFAULT is not None else None

logging.basicConfig(level=logging.WARNING, format='%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

async def handle_message(task_id=None, message=None, alg_msg_queue=None, proxy=None, llm_api_key=None, serpapi_key=None): 
    if "llm_api_key" in message["data"] and len(message["data"]["llm_api_key"].strip()) >= 32:
        llm_api_key = message["data"]["llm_api_key"].strip()
    if KEY_TO_USE_DEFAULT is not None and \
            DEFAULT_LLM_API_KEY is not None and \
            llm_api_key == KEY_TO_USE_DEFAULT:
        # replace with default key
        logger.warning("Using default llm api key")
        llm_api_key = DEFAULT_LLM_API_KEY

    if "serpapi_key" in message["data"] and len(message["data"]["serpapi_key"].strip()) >= 32:
        serpapi_key = message["data"]["serpapi_key"].strip()
    if KEY_TO_USE_DEFAULT is not None and \
            DEFAULT_SERP_API_KEY is not None and \
            serpapi_key == KEY_TO_USE_DEFAULT:
        # replace with default key
        logger.warning("Using default serp api key")
        serpapi_key = DEFAULT_SERP_API_KEY

    idea = message["data"]["idea"].strip() 

    if not llm_api_key:
        alg_msg_queue.put_nowait(format_message(action=MessageType.RunTask.value, msg="Invalid OpenAI key"))
        return
    if not serpapi_key:
        alg_msg_queue.put_nowait(format_message(action=MessageType.RunTask.value, msg="Invalid SerpAPI key"))
        return
    if not idea or len(idea) < 2:
        alg_msg_queue.put_nowait(format_message(action=MessageType.RunTask.value, msg="Invalid task idea"))
        return
    try:
        await startup.startup(idea=idea, task_id=task_id, llm_api_key=llm_api_key, serpapi_key=serpapi_key, proxy=proxy, alg_msg_queue=alg_msg_queue)
        alg_msg_queue.put_nowait(format_message(action=MessageType.RunTask.value, data={'task_id':task_id}, msg="finished"))
    except Exception as e:
        alg_msg_queue.put_nowait(format_message(action=MessageType.RunTask.value, msg=f"{e}"))

        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_message = traceback.format_exception(exc_type, exc_value, exc_traceback)
        logger.error("".join(error_message))

def handle_message_wrapper(task_id=None, message=None, alg_msg_queue=None, proxy=None, llm_api_key=None, serpapi_key=None):
    logger.warning("New task:"+current_process().name)
    asyncio.run(handle_message(task_id, message, alg_msg_queue, proxy, llm_api_key, serpapi_key))

def clear_queue(alg_msg_queue:Queue=None):
    if not Queue:
        return
    try:
        while True:
            alg_msg_queue.get_nowait()
    except queues.Empty:
        pass

# read websocket messages
async def read_msg_worker(websocket=None, alg_msg_queue=None, proxy=None, llm_api_key=None, serpapi_key=None):
    process = None
    async for raw_message in websocket:
        message = json.loads(raw_message)
        if message["action"] == MessageType.Interrupt.value:
            # force interrupt a specific task
            task_id = message["data"]["task_id"]
            if process and process.is_alive() and process.name == task_id:
                logger.warning("Interrupt task:" + process.name)
                process.terminate()
                process = None
            clear_queue(alg_msg_queue=alg_msg_queue)
            alg_msg_queue.put_nowait(format_message(action=MessageType.Interrupt.value, data={'task_id': task_id}))
            alg_msg_queue.put_nowait(format_message(action=MessageType.RunTask.value, data={'task_id': task_id}, msg="finished"))
                
        elif message["action"] == MessageType.RunTask.value:
            # auto interrupt previous task
            if process and process.is_alive():
                logger.warning("Interrupt task:" + process.name)
                process.terminate()
                process = None
                clear_queue(alg_msg_queue=alg_msg_queue)

            task_id = str(uuid.uuid4())
            process = Process(target=handle_message_wrapper, args=(task_id, message, alg_msg_queue, proxy, llm_api_key, serpapi_key))
            process.daemon = True
            process.name = task_id
            process.start()
        
    # auto terminate process
    if process and process.is_alive():
        logger.warning("Interrupt task:" + process.name)
        process.terminate()
        process = None
        clear_queue(alg_msg_queue=alg_msg_queue)
    
    raise websockets.exceptions.ConnectionClosed(0, "websocket closed")

# send
async def send_msg_worker(websocket=None, alg_msg_queue=None):
    while True:
        if alg_msg_queue.empty():
            await asyncio.sleep(0.5)
        else:
            msg = alg_msg_queue.get_nowait()
            print("=====Sending msg=====\n", msg)
            await websocket.send(msg)

async def echo(websocket, proxy=None, llm_api_key=None, serpapi_key=None):
    # audo register
    uid = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S.%f')+'_'+str(uuid.uuid4())
    logger.warning(f"New user registered, uid: {uid}")
    if uid not in user_dict:
        user_dict[uid] = websocket
    else:
        logger.warning(f"Duplicate user, uid: {uid}")
        
    # message handling
    try:
        alg_msg_queue = Queue()
        await asyncio.gather(
            read_msg_worker(websocket=websocket, alg_msg_queue=alg_msg_queue, proxy=proxy, llm_api_key=llm_api_key, serpapi_key=serpapi_key), 
            send_msg_worker(websocket=websocket, alg_msg_queue=alg_msg_queue)
        )
    except websockets.exceptions.ConnectionClosed:
        logger.warning("Websocket closed: remote endpoint going away")
    finally:
        asyncio.current_task().cancel()
        # auto unregister
        logger.warning(f"Auto unregister, uid: {uid}")
       
        if uid in user_dict:
            user_dict.pop(uid)


async def run_service(host: str = "localhost", port: int=9000, proxy: str=None, llm_api_key:str=None, serpapi_key:str=None):
    message_handler = functools.partial(echo, proxy=proxy,llm_api_key=llm_api_key, serpapi_key=serpapi_key)
    async with websockets.serve(message_handler, host, port):
        logger.warning(f"Websocket server started: {host}:{port} {f'[proxy={proxy}]' if proxy else ''}")
        await asyncio.Future()
