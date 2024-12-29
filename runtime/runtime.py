import sys
import os
import time
import redis
import importlib.util
import json
import zipfile
from pathlib import Path

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_INPUT_KEY = os.getenv("REDIS_INPUT_KEY", "metrics")
REDIS_OUTPUT_KEY = os.getenv("REDIS_OUTPUT_KEY", "results")
MONITOR_PERIOD = int(os.getenv("MONITOR_PERIOD", 5))
ENTRY_FUNCTION = os.getenv("ENTRY_FUNCTION", "handler")
ZIP_ENTRY_FILE = os.getenv("ZIP_ENTRY_FUNCTION", "handler")
ZIP_PATH = "/opt/usercode.zip"
PYFILE_PATH = "/opt/usermodule.py"

class Context:
    def __init__(self):
        self.host = REDIS_HOST
        self.port = REDIS_PORT
        self.input_key = REDIS_INPUT_KEY
        self.output_key = REDIS_OUTPUT_KEY
        self.function_getmtime = 0
        self.last_execution = 0
        self.env = {}

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def load_handler_from_pyfile(pyfile_path):
    if not Path(pyfile_path).exists():
        raise FileNotFoundError(f"pyfile not found in specified path: {pyfile_path}")
    
    sys.path.append('/opt')

    spec = importlib.util.spec_from_file_location("usermodule", PYFILE_PATH)
    user_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_module)

    if not hasattr(user_module, "handler"):
        raise AttributeError("handler function not found in pyfile.")
    return getattr(user_module, "handler")

def load_handler_from_zip(zip_path, zip_entry_file, entry_function):
    if not Path(zip_path).exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")
    
    extract_dir = "/tmp/usercode"
    os.makedirs(extract_dir, exist_ok=True)

    #extract_dir = Path("/tmp/usercode")

    # if extract_dir.exists():
    #     for item in extract_dir.iterdir():
    #         if item.is_file():
    #             item.unlink()
    #         elif item.is_dir():
    #             import shutil
    #             shutil.rmtree(item)
    # extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    sys.path.append(extract_dir)

    spec = importlib.util.spec_from_file_location(zip_entry_file, os.path.join(extract_dir, f"{zip_entry_file}.py"))
    user_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_module)

    if not hasattr(user_module, entry_function):
        raise AttributeError(f"Function '{entry_function}' not found in user module.")
    return getattr(user_module, entry_function)

def monitor_redis():
    last_data = None
    handler = None
    context = Context()

    while True:
        try:
            data = redis_client.get(REDIS_INPUT_KEY)

            if data != last_data:
                last_data = data

                if data is not None:
                    input_data = json.loads(data.decode("utf-8"))

                    zip_mtime = Path(ZIP_PATH).stat().st_mtime

                    if handler is None:
                        if os.path.isfile(ZIP_PATH):
                            print("runtime: Using ZIP file.")
                            handler = load_handler_from_zip(ZIP_PATH, ZIP_ENTRY_FILE, ENTRY_FUNCTION)
                            context.function_getmtime = os.path.getmtime(ZIP_PATH)
                        else:
                            print("runtime: Using pyfile.")
                            handler = load_handler_from_pyfile(PYFILE_PATH)
                            context.function_getmtime = os.path.getmtime(PYFILE_PATH)

                        context.function_getmtime = zip_mtime

                    context.last_execution = time.time()

                    result = handler(input_data, context)

                    redis_client.set(REDIS_OUTPUT_KEY, json.dumps(result).encode("utf-8"))

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(MONITOR_PERIOD)

if __name__ == "__main__":
    monitor_redis()
