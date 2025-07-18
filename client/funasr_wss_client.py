# -*- encoding: utf-8 -*-
import os
import time
import websockets, ssl
import asyncio
import argparse
import json
import traceback
from multiprocessing import Process
from queue import Queue

import logging
logging.basicConfig(level=logging.ERROR)


# --- 新增：自动定位项目根目录下的hotwords.txt ---
# 假设此脚本位于 "client" 文件夹内，项目根目录是其上一级
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
    HOTWORD_FILE_PATH = os.path.join(PROJECT_ROOT, 'hotwords.txt')
except NameError:
    # 在某些交互式环境 __file__ 可能未定义
    HOTWORD_FILE_PATH = "hotwords.txt"


# --- 新增：重构的热词加载函数 ---
def _load_hotwords(file_path):
    """
    从指定路径加载热词文件，并返回JSON格式的字符串。
    如果文件不存在或内容格式不正确，则返回空字符串。
    """
    if not os.path.exists(file_path):
        # print(f"Info: Hotword file not found at '{file_path}'. Proceeding without hotwords.")
        return ""

    fst_dict = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                words = line.split()
                if len(words) < 2:
                    print(f"Warning: Hotword line format error, skipping: '{line}'")
                    continue
                try:
                    # 将除最后一个词外的所有部分作为热词，最后一个词作为权重
                    fst_dict[" ".join(words[:-1])] = int(words[-1])
                except ValueError:
                    print(f"Warning: Hotword weight format error, skipping: '{line}'")
                    continue
        if fst_dict:
            print(f"Successfully loaded hotwords from '{file_path}'")
            return json.dumps(fst_dict)
        else:
            return ""
    except Exception as e:
        print(f"Error loading hotword file '{file_path}': {e}")
        return ""

# --- 原有代码，但进行修改 ---

parser = argparse.ArgumentParser()
parser.add_argument(
    "--host", type=str, default="localhost", required=False, help="host ip, localhost, 0.0.0.0"
)
parser.add_argument("--port", type=int, default=10095, required=False, help="grpc server port")
parser.add_argument("--chunk_size", type=str, default="5, 10, 5", help="chunk")
parser.add_argument("--encoder_chunk_look_back", type=int, default=4, help="chunk")
parser.add_argument("--decoder_chunk_look_back", type=int, default=0, help="chunk")
parser.add_argument("--chunk_interval", type=int, default=10, help="chunk")
# parser.add_argument("--hotword",... # 已移除此行
parser.add_argument("--audio_in", type=str, default=None, help="audio_in")
parser.add_argument("--audio_fs", type=int, default=16000, help="audio_fs")
parser.add_argument(
    "--send_without_sleep",
    action="store_true",
    default=True,
    help="if audio_in is set, send_without_sleep",
)
parser.add_argument("--thread_num", type=int, default=1, help="thread_num")
parser.add_argument("--words_max_print", type=int, default=10000, help="chunk")
parser.add_argument("--output_dir", type=str, default=None, help="output_dir")
parser.add_argument("--ssl", type=int, default=1, help="1 for ssl connect, 0 for no ssl")
parser.add_argument("--use_itn", type=int, default=1, help="1 for using itn, 0 for not itn")
parser.add_argument("--mode", type=str, default="2pass", help="offline, online, 2pass")

args = parser.parse_args()
args.chunk_size = [int(x) for x in args.chunk_size.split(",")]
print(args)

voices = Queue()
offline_msg_done = False

if args.output_dir is not None:
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)


async def record_microphone():
    is_finished = False
    import pyaudio
    
    global voices
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    chunk_size = 60 * args.chunk_size[1] / args.chunk_interval
    CHUNK = int(RATE / 1000 * chunk_size)

    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )
    
    # --- 修改：调用新的热词加载函数 ---
    hotword_msg = _load_hotwords(HOTWORD_FILE_PATH)

    use_itn = True
    if args.use_itn == 0:
        use_itn = False

    message = json.dumps(
        {
            "mode": args.mode,
            "chunk_size": args.chunk_size,
            "chunk_interval": args.chunk_interval,
            "encoder_chunk_look_back": args.encoder_chunk_look_back,
            "decoder_chunk_look_back": args.decoder_chunk_look_back,
            "wav_name": "microphone",
            "is_speaking": True,
            "hotwords": hotword_msg,
            "itn": use_itn,
        }
    )
    await websocket.send(message)
    while True:
        data = stream.read(CHUNK)
        message = data
        await websocket.send(message)
        await asyncio.sleep(0.005)


async def record_from_scp(chunk_begin, chunk_size):
    global voices
    is_finished = False
    if args.audio_in.endswith(".scp"):
        f_scp = open(args.audio_in)
        wavs = f_scp.readlines()
    else:
        wavs = [args.audio_in]

    # --- 修改：调用新的热词加载函数 ---
    hotword_msg = _load_hotwords(HOTWORD_FILE_PATH)

    sample_rate = args.audio_fs
    wav_format = "pcm"
    use_itn = True
    if args.use_itn == 0:
        use_itn = False

    if chunk_size > 0:
        wavs = wavs[chunk_begin : chunk_begin + chunk_size]
    for wav in wavs:
        wav_splits = wav.strip().split()

        wav_name = wav_splits[0] if len(wav_splits) > 1 else "demo"
        wav_path = wav_splits[1] if len(wav_splits) > 1 else wav_splits[0]
        if not len(wav_path.strip()) > 0:
            continue
        if wav_path.endswith(".pcm"):
            with open(wav_path, "rb") as f:
                audio_bytes = f.read()
        elif wav_path.endswith(".wav"):
            import wave

            with wave.open(wav_path, "rb") as wav_file:
                params = wav_file.getparams()
                sample_rate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())
                audio_bytes = bytes(frames)
        else:
            wav_format = "others"
            with open(wav_path, "rb") as f:
                audio_bytes = f.read()

        stride = int(60 * args.chunk_size[1] / args.chunk_interval / 1000 * sample_rate * 2)
        chunk_num = (len(audio_bytes) - 1) // stride + 1
        
        # send first time
        message = json.dumps(
            {
                "mode": args.mode,
                "chunk_size": args.chunk_size,
                "chunk_interval": args.chunk_interval,
                "encoder_chunk_look_back": args.encoder_chunk_look_back,
                "decoder_chunk_look_back": args.decoder_chunk_look_back,
                "audio_fs": sample_rate,
                "wav_name": wav_name,
                "wav_format": wav_format,
                "is_speaking": True,
                "hotwords": hotword_msg, # 使用加载好的热词
                "itn": use_itn,
            }
        )
        
        await websocket.send(message)
        is_speaking = True
        for i in range(chunk_num):

            beg = i * stride
            data = audio_bytes[beg : beg + stride]
            message = data
            await websocket.send(message)
            if i == chunk_num - 1:
                is_speaking = False
                message = json.dumps({"is_speaking": is_speaking})
                await websocket.send(message)

            sleep_duration = (
                0.001
                if args.mode == "offline"
                else 60 * args.chunk_size[1] / args.chunk_interval / 1000
            )

            await asyncio.sleep(sleep_duration)

    if not args.mode == "offline":
        await asyncio.sleep(2)
    
    if args.mode == "offline":
        global offline_msg_done
        while not offline_msg_done:
            await asyncio.sleep(1)

    await websocket.close()


async def message(id):
    global websocket, voices, offline_msg_done
    text_print = ""
    text_print_2pass_online = ""
    text_print_2pass_offline = ""
    if args.output_dir is not None:
        ibest_writer = open(
            os.path.join(args.output_dir, "text.{}".format(id)), "a", encoding="utf-8"
        )
    else:
        ibest_writer = None
    try:
        while True:
            meg = await websocket.recv()
            meg = json.loads(meg)
            wav_name = meg.get("wav_name", "demo")
            text = meg["text"]
            timestamp = ""
            offline_msg_done = meg.get("is_final", False)
            if "timestamp" in meg:
                timestamp = meg["timestamp"]

            if ibest_writer is not None:
                if timestamp != "":
                    text_write_line = "{}\t{}\t{}\n".format(wav_name, text, timestamp)
                else:
                    text_write_line = "{}\t{}\n".format(wav_name, text)
                ibest_writer.write(text_write_line)

            if "mode" not in meg:
                continue
            if meg["mode"] == "online":
                text_print += "{}".format(text)
                text_print = text_print[-args.words_max_print :]
                os.system("clear")
                print("\rpid" + str(id) + ": " + text_print)
            elif meg["mode"] == "offline":
                if timestamp != "":
                    text_print += "{} timestamp: {}".format(text, timestamp)
                else:
                    text_print += "{}".format(text)
                print("\rpid" + str(id) + ": " + wav_name + ": " + text_print)
                offline_msg_done = True
            else:
                if meg["mode"] == "2pass-online":
                    text_print_2pass_online += "{}".format(text)
                    text_print = text_print_2pass_offline + text_print_2pass_online
                else:
                    text_print_2pass_online = ""
                    text_print = text_print_2pass_offline + "{}".format(text)
                    text_print_2pass_offline += "{}".format(text)
                text_print = text_print[-args.words_max_print :]
                os.system("clear")
                print("\rpid" + str(id) + ": " + text_print)

    except Exception as e:
        # 忽略正常的连接关闭异常
        if not isinstance(e, websockets.exceptions.ConnectionClosedOK) and not isinstance(e, websockets.exceptions.ConnectionClosedError):
             print("Exception:", e)


async def ws_client(id, chunk_begin, chunk_size):
    if args.audio_in is None:
        chunk_begin = 0
        chunk_size = 1
    global websocket, voices, offline_msg_done

    for i in range(chunk_begin, chunk_begin + chunk_size):
        offline_msg_done = False
        voices = Queue()
        if args.ssl == 1:
            ssl_context = ssl.SSLContext()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://{}:{}".format(args.host, args.port)
        else:
            uri = "ws://{}:{}".format(args.host, args.port)
            ssl_context = None
        print("connect to", uri)
        async with websockets.connect(
            uri, subprotocols=["binary"], ping_interval=None, ssl=ssl_context
        ) as websocket:
            if args.audio_in is not None:
                task = asyncio.create_task(record_from_scp(i, 1))
            else:
                task = asyncio.create_task(record_microphone())
            task3 = asyncio.create_task(message(str(id) + "_" + str(i)))
            await asyncio.gather(task, task3)
    exit(0)


def one_thread(id, chunk_begin, chunk_size):
    # For Windows, create a new event loop for each process
    if os.name == 'nt':
        asyncio.set_event_loop(asyncio.new_event_loop())
        
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ws_client(id, chunk_begin, chunk_size))
    loop.run_forever()


if __name__ == "__main__":
    if args.audio_in is None:
        p = Process(target=one_thread, args=(0, 0, 0))
        p.start()
        p.join()
        print("end")
    else:
        if args.audio_in.endswith(".scp"):
            f_scp = open(args.audio_in)
            wavs = f_scp.readlines()
        else:
            wavs = [args.audio_in]
        
        total_len = len(wavs)
        if total_len >= args.thread_num:
            chunk_size = total_len // args.thread_num
            remain_wavs = total_len % args.thread_num
        else:
            # 如果文件数小于线程数，则每个线程处理一个文件，多余线程空闲
            args.thread_num = total_len
            chunk_size = 1
            remain_wavs = 0

        process_list = []
        chunk_begin = 0
        for i in range(args.thread_num):
            if chunk_begin >= total_len:
                break
            now_chunk_size = chunk_size + 1 if i < remain_wavs else chunk_size
            
            p = Process(target=one_thread, args=(i, chunk_begin, now_chunk_size))
            chunk_begin += now_chunk_size
            p.start()
            process_list.append(p)

        for p in process_list:
            p.join()

        print("end")
