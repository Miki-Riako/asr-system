from multiprocessing import Queue, Process
import websockets, ssl, asyncio, json, os, argparse
import wave # For .wav file handling

parser = argparse.ArgumentParser(description="ASR Client for Single Audio File Processing")
parser.add_argument("--host", type=str, default="localhost", help="Host IP for the WebSocket server (e.g., localhost, 0.0.0.0).")
parser.add_argument("--port", type=int, default=10095, help="Port for the WebSocket server.")
parser.add_argument("--audio_in", type=str, required=True, help="Path to the input audio file (e.g., .wav, .pcm).")
parser.add_argument("--hotword", type=str, default="", help="Path to the hotword file (optional). If provided, ASR will also run with hotwords.")
parser.add_argument("--ssl", type=int, default=1, choices=[0, 1], help="Use SSL/WSS. 1 for yes, 0 for no.")
parser.add_argument("--use_itn", type=int, default=1, choices=[0, 1], help="Use Inverse Text Normalization (ITN). 1 for yes, 0 for no.")

args = parser.parse_args()
args.chunk_size = [5, 10, 5]
args.chunk_interval = 10
args.audio_fs = 16000
args.thread_num = 1

voices = Queue()
offline_msg_done = False

async def record_from_file(file_path):
    global voices
    
    wav_name = os.path.basename(file_path)
    audio_bytes = b''
    sample_rate = args.audio_fs
    wav_format = "pcm"

    try:
        if file_path.endswith(".pcm"):
            with open(file_path, "rb") as f:
                audio_bytes = f.read()
        elif file_path.endswith(".wav"):
            with wave.open(file_path, "rb") as wav_file:
                sample_rate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())
                audio_bytes = bytes(frames)        
        else:
            wav_format = "others"
            with open(file_path, "rb") as f:
                audio_bytes = f.read()
    except FileNotFoundError:
        print(f"Error: Audio file not found at {file_path}")
        return
    except Exception as e:
        print(f"Error reading audio file {file_path}: {e}")
        return

    fst_dict = {}
    hotword_msg = ""
    if args.hotword.strip() != "":
        try:
            with open(args.hotword, encoding='utf-8') as f_hotword:
                hot_lines = f_hotword.readlines()
                for line in hot_lines:
                    words = line.strip().split(" ")
                    if len(words) < 2:
                        continue
                    try:
                        fst_dict[" ".join(words[:-1])] = int(words[-1])
                    except ValueError:
                        continue
            hotword_msg=json.dumps(fst_dict)
        except FileNotFoundError:
            print(f"Warning: Hotword file '{args.hotword}' not found. Proceeding without hotwords.")
            hotword_msg = ""

    use_itn=True
    if args.use_itn == 0:
        use_itn=False

    stride = int(60 * args.chunk_size[1] / args.chunk_interval / 1000 * sample_rate * 2)
    if stride == 0:
        stride = 1600
        
    chunk_num = (len(audio_bytes) - 1) // stride + 1 if stride > 0 else 1

    message = json.dumps({"mode": "offline", "chunk_size": args.chunk_size, "chunk_interval": args.chunk_interval, "audio_fs":sample_rate, "wav_name": wav_name, "wav_format": wav_format, "is_speaking": True, "hotwords":hotword_msg, "itn": use_itn})
    await websocket.send(message)
    
    is_speaking = True
    for i in range(chunk_num):
        beg = i * stride
        data = audio_bytes[beg:min(beg + stride, len(audio_bytes))]
        if not data:
            break
        await websocket.send(data)
        if i == chunk_num - 1:
            is_speaking = False
            message = json.dumps({"is_speaking": is_speaking})
            await websocket.send(message)
        
        sleep_duration = 0.001
        await asyncio.sleep(sleep_duration)
    
    global offline_msg_done
    while not offline_msg_done:
        await asyncio.sleep(0.1)

async def message(result_queue):
    global websocket, offline_msg_done
    try:
        while True:
            meg = await websocket.recv()
            if isinstance(meg, str):
                meg_dict = json.loads(meg)
                text = meg_dict.get("text", "")
                
                if meg_dict.get("mode") == "offline":
                    result_queue.put(text)
                    offline_msg_done = True
                    break
                elif meg_dict.get("is_final", False):
                    result_queue.put(text)
                    offline_msg_done = True
                    break
                else:
                    result_queue.put(text)
            else:
                pass
    except websockets.exceptions.ConnectionClosedOK:
        print("WebSocket connection closed normally.")
    except Exception as e:
        print(f"Exception in message receiver: {e}")
    finally:
        offline_msg_done = True

async def ws_client(id, audio_path, result_queue):
    global websocket, voices, offline_msg_done

    offline_msg_done = False

    if args.ssl == 1:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        uri = f"wss://{args.host}:{args.port}"
    else:
        uri = f"ws://{args.host}:{args.port}"
        ssl_context = None

    try:
        async with websockets.connect(uri, subprotocols=["binary"], ping_interval=None, ssl=ssl_context) as websocket_conn:
            websocket = websocket_conn
            
            audio_task = asyncio.create_task(record_from_file(audio_path))
            message_task = asyncio.create_task(message(result_queue))
            
            await asyncio.gather(audio_task, message_task)
    except Exception as e:
        print(f"WebSocket client error for {audio_path}: {e}")
    finally:
        offline_msg_done = True

def run_audio(audio_file_path, hotwords_file_path=""):
    global args
    args.audio_in = audio_file_path
    args.hotword = hotwords_file_path

    result_queue = Queue()

    p = Process(target=one_thread, args=(0, 0, 1, result_queue))
    p.start()
    p.join()

    result_list = []
    while not result_queue.empty():
        result_list.append(result_queue.get())
    
    processed_result = "\n".join(set(result_list)).replace(' ', '').replace('，', '')
    return processed_result

def one_thread(id, chunk_begin, chunk_size, result_queue):
    asyncio.get_event_loop().run_until_complete(ws_client(id, args.audio_in, result_queue))

if __name__ == '__main__':
    
    input_audio_path = args.audio_in
    hotword_file_path = args.hotword

    print(f"--- Processing Audio: {input_audio_path} ---")

    print("\n--- ASR Result (No Hotwords) ---")
    result_no_hotword = run_audio(input_audio_path, "").strip()
    print(f"Result: {result_no_hotword}")

    result_with_hotword = ""
    if hotword_file_path and os.path.exists(hotword_file_path):
        print(f"\n--- ASR Result (With Hotwords from: {hotword_file_path}) ---")
        result_with_hotword = run_audio(input_audio_path, hotword_file_path).strip()
        print(f"Result: {result_with_hotword}")
    else:
        print("\n--- No hotword file provided or found, skipping ASR with hotwords. ---")
    
    print("\n--- Processing Finished ---")
    # python hotwords_proc.py --host localhost --port 10095 --audio_in ./samples/audio/example.wav --hotword ./samples/hotwords.txt
