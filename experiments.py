import csv
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from multiprocessing import Queue, Process
import websockets, ssl, asyncio, json, os, argparse

# DEBUG=8
DEBUG = float('inf')

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="localhost", required=False, help="host ip, localhost, 0.0.0.0")
parser.add_argument("--port", type=int, default=10095, required=False, help="grpc server port")

args = parser.parse_args()
args.chunk_size = [5, 10, 5]
args.chunk_interval = 10
args.audio_fs = 16000
args.thread_num = 1
args.ssl = 1
args.use_itn = 1

voices = Queue()
offline_msg_done=False

async def record_microphone():
    import pyaudio
    global voices
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    chunk_size = 60 * args.chunk_size[1] / args.chunk_interval
    CHUNK = int(RATE / 1000 * chunk_size)

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    fst_dict = {}
    hotword_msg = ""
    if args.hotword.strip() != "":
        f_scp = open(args.hotword)
        hot_lines = f_scp.readlines()
        for line in hot_lines:
            words = line.strip().split(" ")
            if len(words) < 2:
                continue
            try:
                fst_dict[" ".join(words[:-1])] = int(words[-1])
            except ValueError:
                continue
        hotword_msg=json.dumps(fst_dict)

    use_itn=True
    if args.use_itn == 0:
        use_itn=False
    
    message = json.dumps({"mode": "offline", "chunk_size": args.chunk_size, "chunk_interval": args.chunk_interval, "wav_name": "microphone", "is_speaking": True, "hotwords":hotword_msg, "itn": use_itn})
    await websocket.send(message)
    while True:
        data = stream.read(CHUNK)
        message = data
        await websocket.send(message)
        await asyncio.sleep(0.005)

async def record_from_scp(chunk_begin, chunk_size):
    global voices
    if args.audio_in.endswith(".scp"):
        f_scp = open(args.audio_in)
        wavs = f_scp.readlines()
    else:
        wavs = [args.audio_in]

    fst_dict = {}
    hotword_msg = ""
    if args.hotword.strip() != "":
        f_scp = open(args.hotword)
        hot_lines = f_scp.readlines()
        for line in hot_lines:
            words = line.strip().split(" ")
            if len(words) < 2:
                continue
            try:
                fst_dict[" ".join(words[:-1])] = int(words[-1])
            except ValueError:
                continue
        hotword_msg=json.dumps(fst_dict)

    sample_rate = args.audio_fs
    wav_format = "pcm"
    use_itn=True
    if args.use_itn == 0:
        use_itn=False
    if chunk_size > 0:
        wavs = wavs[chunk_begin:chunk_begin + chunk_size]
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
                sample_rate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())
                audio_bytes = bytes(frames)        
        else:
            wav_format = "others"
            with open(wav_path, "rb") as f:
                audio_bytes = f.read()

        stride = int(60 * args.chunk_size[1] / args.chunk_interval / 1000 * sample_rate * 2)
        chunk_num = (len(audio_bytes) - 1) // stride + 1
        message = json.dumps({"mode": "offline", "chunk_size": args.chunk_size, "chunk_interval": args.chunk_interval, "audio_fs":sample_rate, "wav_name": wav_name, "wav_format": wav_format, "is_speaking": True, "hotwords":hotword_msg, "itn": use_itn})
        await websocket.send(message)
        is_speaking = True
        for i in range(chunk_num):
            beg = i * stride
            data = audio_bytes[beg:beg + stride]
            message = data
            await websocket.send(message)
            if i == chunk_num - 1:
                is_speaking = False
                message = json.dumps({"is_speaking": is_speaking})
                await websocket.send(message)
            
            sleep_duration = 0.001
            await asyncio.sleep(sleep_duration)
    
    global offline_msg_done
    while not offline_msg_done:
        await asyncio.sleep(1)
    
    await websocket.close()

async def message(id, result_queue):
    global websocket, voices, offline_msg_done
    try:
        while True:
            meg = await websocket.recv()
            meg = json.loads(meg)
            text = meg["text"]
            offline_msg_done = meg.get("is_final", False)
            result_queue.put(text)
            if 'mode' not in meg:
                continue
            if meg["mode"] == "offline":
                result_queue.put(text)
                offline_msg_done = True
    except Exception as e:
        print("Exception:", e)

async def ws_client(id, chunk_begin, chunk_size, result_queue):
    global websocket, voices, offline_msg_done
    for i in range(chunk_begin, chunk_begin+chunk_size):
        offline_msg_done=False
        voices = Queue()
        if args.ssl == 1:
            ssl_context = ssl.SSLContext()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://{}:{}".format(args.host, args.port)
        else:
            uri = "ws://{}:{}".format(args.host, args.port)
            ssl_context = None
        async with websockets.connect(uri, subprotocols=["binary"], ping_interval=None, ssl=ssl_context) as websocket:
            if args.audio_in is not None:
                task = asyncio.create_task(record_from_scp(i, 1))
            else:
                task = asyncio.create_task(record_microphone())
            task3 = asyncio.create_task(message(str(id)+"_"+str(i), result_queue))
            await asyncio.gather(task, task3)
    exit(0)
    
def one_thread(id, chunk_begin, chunk_size, result_queue):
    asyncio.get_event_loop().run_until_complete(ws_client(id, chunk_begin, chunk_size, result_queue))
    asyncio.get_event_loop().run_forever()


def run_audio(audio_file, hotwords=""):
    args.audio_in = audio_file
    args.hotword = hotwords
    result_queue = Queue()

    if args.audio_in is None:
        p = Process(target=one_thread, args=(0, 0, 0, result_queue))
        p.start()
        p.join()
    else:
        if args.audio_in.endswith(".scp"):
            with open(args.audio_in) as f_scp:
                wavs = f_scp.readlines()
        else:
            wavs = [args.audio_in]
        total_len = len(wavs)
        
        if total_len >= args.thread_num:
            chunk_size = int(total_len / args.thread_num)
            remain_wavs = total_len - chunk_size * args.thread_num
        else:
            chunk_size = 1
            remain_wavs = 0
        
        process_list = []
        chunk_begin = 0
        for i in range(args.thread_num):
            now_chunk_size = chunk_size
            if remain_wavs > 0:
                now_chunk_size = chunk_size + 1
                remain_wavs -= 1
            p = Process(target=one_thread, args=(i, chunk_begin, now_chunk_size, result_queue))
            chunk_begin += now_chunk_size
            p.start()
            process_list.append(p)
        
        for p in process_list:
            p.join()
    result = []
    while not result_queue.empty():
        result.append(result_queue.get())
    return "\n".join(set(result))

class Experiments:
    def __init__(self):
        self.hotwords_path  = './samples/python/speech_asr_aishell_hotwords_testsets/hotwords.txt'
        self.reference_path = './samples/python/speech_asr_aishell_hotwords_testsets/speech_asr_aishell_hotwords_testsets.csv'
        self.reference = []
        self.results   = []
        self.cnt = 0
        
        self.hotwords = self.load_hotwords(self.hotwords_path)
        self.pre_process()
    
    def load_hotwords(self, path):
        hotwords = set()
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().split()[0]
                hotwords.add(word)
        return hotwords
    
    @staticmethod
    def min_distance(word1: str, word2: str) -> int:
        row = len(word1) + 1
        column = len(word2) + 1
        cache = [ [0]*column for _ in range(row) ]
        for i in range(row):
            for j in range(column):
                if i ==0 and j ==0:
                    cache[i][j] = 0
                elif i == 0 and j!=0:
                    cache[i][j] = j
                elif j == 0 and i!=0:
                    cache[i][j] = i
                else:
                    if word1[i-1] == word2[j-1]:
                        cache[i][j] = cache[i-1][j-1]
                    else:
                        replace = cache[i-1][j-1] + 1
                        insert = cache[i][j-1] + 1
                        remove = cache[i-1][j] + 1
                        cache[i][j] = min(replace, insert, remove)
        return cache[row-1][column-1]

    def pre_process(self):
        ...

    def process_data(self):
        with open(self.reference_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for i, row in enumerate(reader):
                if i >= DEBUG:
                    break
                input_audio, reference = row
                input_audio = input_audio
                reference = reference.replace(' ', '')
                result_no_hotword, result_with_hotword = self.generate(input_audio)
                cer_no_hotword, ref_len_no_hotword = self.calculate_cer(reference, result_no_hotword)
                cer_with_hotword, ref_len_with_hotword = self.calculate_cer(reference, result_with_hotword)
                precision_no_hotword, recall_no_hotword = self.calculate_precision_recall(reference, result_no_hotword)
                precision_with_hotword, recall_with_hotword = self.calculate_precision_recall(reference, result_with_hotword)
                self.results.append({
                    "input_audio": input_audio,
                    "reference": reference,
                    "result_no_hotword": result_no_hotword,
                    "result_with_hotword": result_with_hotword,
                    "cer_no_hotword": cer_no_hotword,
                    "cer_with_hotword": cer_with_hotword,
                    "ref_len_no_hotword": ref_len_no_hotword,
                    "ref_len_with_hotword": ref_len_with_hotword,
                    "precision_no_hotword": precision_no_hotword,
                    "recall_no_hotword": recall_no_hotword,
                    "precision_with_hotword": precision_with_hotword,
                    "recall_with_hotword": recall_with_hotword,
                })

    def generate(self, input_audio: str):
        try:
            print(str(self.cnt)+": "+input_audio)
            self.cnt += 1
            result_no_hotword = run_audio(input_audio).replace('，', '')
            result_with_hotword = run_audio(input_audio, self.hotwords_path).replace('，', '')
            return result_no_hotword.replace(' ', '').split("\n")[0], result_with_hotword.replace(' ', '').split("\n")[0]
        except Exception as e:
            print(f"Error generating ASR results: {e}")
            return "", ""

    def calculate_precision_recall(self, reference: str, hypothesis: str):
        ref_hotwords = set([word for word in self.hotwords if word in reference])
        hyp_hotwords = set([word for word in self.hotwords if word in hypothesis])
        true_positives = len(ref_hotwords & hyp_hotwords)
        precision = true_positives / len(hyp_hotwords) if hyp_hotwords else 0
        recall = true_positives / len(ref_hotwords) if ref_hotwords else 0
        return precision, recall

    def calculate_cer(self, reference: str, hypothesis: str):
        distance = self.min_distance(reference, hypothesis)
        len_ref = len(reference)
        if len_ref == 0:
            return 0, 0
        return (distance / len(reference)) * 100, len(reference)

    def post_process(self):
        # Calculate total CER
        avg_no_hotword = sum(result["ref_len_no_hotword"] for result in self.results)
        avg_with_hotword = sum(result["ref_len_with_hotword"] for result in self.results)
        self.sum_data = len(self.results)
        self.avg_cer_no_hotword = 0.0 if self.sum_data < 1 else sum(result["cer_no_hotword"] for result in self.results) / self.sum_data
        self.avg_cer_with_hotword = 0.0 if self.sum_data < 1 else sum(result["cer_with_hotword"] for result in self.results) / self.sum_data
        self.weighted_cer_no_hotword = 0.0 if avg_no_hotword < 1 else sum(result["cer_no_hotword"] * result["ref_len_no_hotword"] for result in self.results) / avg_no_hotword
        self.weighted_cer_with_hotword = 0.0 if avg_with_hotword < 1 else sum(result["cer_with_hotword"] * result["ref_len_with_hotword"] for result in self.results) / avg_with_hotword

        # Calculate Precision, Recall, and F1-Score
        self.avg_precision_no_hotword = sum(result["precision_no_hotword"] for result in self.results) / self.sum_data
        self.avg_recall_no_hotword = sum(result["recall_no_hotword"] for result in self.results) / self.sum_data
        self.avg_precision_with_hotword = sum(result["precision_with_hotword"] for result in self.results) / self.sum_data
        self.avg_recall_with_hotword = sum(result["recall_with_hotword"] for result in self.results) / self.sum_data
        self.f1_score_no_hotword = 2 * (self.avg_precision_no_hotword * self.avg_recall_no_hotword) / (self.avg_precision_no_hotword + self.avg_recall_no_hotword) if (self.avg_precision_no_hotword + self.avg_recall_no_hotword) > 0 else 0
        self.f1_score_with_hotword = 2 * (self.avg_precision_with_hotword * self.avg_recall_with_hotword) / (self.avg_precision_with_hotword + self.avg_recall_with_hotword) if (self.avg_precision_with_hotword + self.avg_recall_with_hotword) > 0 else 0

        # Plot image
        self.plot('output.png')
        self.plot('output_new.png', True)

    def plot(self, filename, smooth=False):
        cer_no_hotword = [result["cer_no_hotword"] for result in self.results]
        cer_with_hotword = [result["cer_with_hotword"] for result in self.results]
        bins = np.arange(0, max(cer_no_hotword + cer_with_hotword) + 5, 5)
        count_no_hotword, _ = np.histogram(cer_no_hotword, bins=bins)
        count_with_hotword, _ = np.histogram(cer_with_hotword, bins=bins)
        x = bins[:-1] + 2.5
        plt.figure(figsize=(12, 6))

        if smooth:
            x_smooth = np.linspace(x.min(), x.max(), 300)
            spl_no_hotword = make_interp_spline(x, count_no_hotword, k=3)
            spl_with_hotword = make_interp_spline(x, count_with_hotword, k=3)
            count_no_hotword_smooth = spl_no_hotword(x_smooth)
            count_with_hotword_smooth = spl_with_hotword(x_smooth)
            plt.plot(x_smooth, count_no_hotword_smooth, label='No Hotword', color='blue')
            plt.plot(x_smooth, count_with_hotword_smooth, label='With Hotword', color='red')
        else:
            plt.scatter(x, count_no_hotword, label='No Hotword', color='blue')
            plt.scatter(x, count_with_hotword, label='With Hotword', color='red')

        plt.xlabel('CER Range')
        plt.ylabel('Count')
        plt.legend(loc='lower left', title=f'Counts of data: {self.sum_data}')
        plt.title('CER Distribution')
        plt.savefig('./images/' + filename)
        plt.show()

    def show(self):
        print()
        for result in self.results:
            print(f"\nInput Audio: {result['input_audio']}")
            print(f"Reference:         {result['reference']}")
            print(f"No Hotwords:       {result['result_no_hotword']}")
            print(f"With Hotwords:     {result['result_with_hotword']}")
            print(f"CER(%) no hotwords:   {result['cer_no_hotword']:.4f}")
            print(f"CER(%) with hotwords: {result['cer_with_hotword']:.4f}")

        print()
        print(f"Average CER(%) no hotwords:    {self.avg_cer_no_hotword:.4f}")
        print(f"Average CER(%) with hotwords:  {self.avg_cer_with_hotword:.4f}")
        print(f"Weighted CER(%) no hotwords:   {self.weighted_cer_no_hotword:.4f}")
        print(f"Weighted CER(%) with hotwords: {self.weighted_cer_with_hotword:.4f}")
        print(f"Counts of data:                {self.sum_data}")

        print(f"\nHotwords Metrics (No Hotwords):")
        print(f"Precision: {self.avg_precision_no_hotword:.4f}")
        print(f"Recall:    {self.avg_recall_no_hotword:.4f}")
        print(f"F1-Score: {self.f1_score_no_hotword:.4f}")

        print(f"\nHotwords Metrics (With Hotwords):")
        print(f"Precision: {self.avg_precision_with_hotword:.4f}")
        print(f"Recall:    {self.avg_recall_with_hotword:.4f}")
        print(f"F1-Score: {self.f1_score_with_hotword:.4f}")

if __name__ == '__main__':
    e = Experiments()
    e.process_data()
    e.post_process()
    e.show()
