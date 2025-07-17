# File: client/funasr_realtime_chunk_client.py
# 这是一个专门用于处理实时音频片段的新脚本

import asyncio
import argparse
import json
import logging
import os
import websockets
import wave

# 只报告严重错误，保持输出干净
logging.basicConfig(level=logging.CRITICAL)

# 定义全局变量来存储最终结果
final_result = ""
# 使用 asyncio.Event 来同步任务，确保在获取结果前任务已完成
is_done = asyncio.Event()

async def process_audio_chunk(websocket, audio_path):
    """读取WAV文件，并将其发送到FunASR进行识别"""
    try:
        with wave.open(audio_path, "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            audio_bytes = wav_file.readframes(wav_file.getnframes())
    except Exception as e:
        logging.error(f"无法读取临时WAV文件: {e}")
        is_done.set()
        return

    # FunASR的WebSocket连接配置
    config = {
        "mode": "offline",
        "chunk_size": [5, 10, 5],
        "wav_name": "realtime_chunk",
        "is_speaking": True,
        "hotwords": "",
        "itn": True,
        "audio_fs": sample_rate,
    }

    try:
        # 发送配置
        await websocket.send(json.dumps(config))
        # 发送音频数据
        await websocket.send(audio_bytes)
        # 发送结束标记
        await websocket.send(json.dumps({"is_speaking": False}))

        # 等待并接收结果
        while not is_done.is_set():
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            response_data = json.loads(response)
            
            # 我们只关心包含最终文本的'offline'模式结果
            if response_data.get("mode") == "offline" and "text" in response_data:
                global final_result
                final_result = response_data["text"]
                break # 收到结果后即可退出循环
    except Exception as e:
        logging.error(f"与FunASR通信时出错: {e}")
    finally:
        # 确保is_done事件被设置，以允许主程序退出
        is_done.set()

async def main(host, port, audio_path):
    """主函数，建立连接并处理音频"""
    uri = f"ws://{host}:{port}"
    try:
        # 连接到FunASR的WebSocket服务
        async with websockets.connect(uri, subprotocols=["binary"], ping_interval=None) as websocket:
            await process_audio_chunk(websocket, audio_path)
    except Exception as e:
        logging.error(f"无法连接到FunASR WebSocket服务于 {uri}: {e}")
        is_done.set()


if __name__ == "__main__":
    # 从命令行接收必要的参数
    parser = argparse.ArgumentParser(description="FunASR实时音频块识别客户端")
    parser.add_argument("--host", default="127.0.0.1", help="FunASR服务地址")
    parser.add_argument("--port", type=int, default=10095, help="FunASR服务端口")
    parser.add_argument("--audio_in", required=True, help="输入的WAV音频文件路径")
    args = parser.parse_args()

    # 运行主异步函数
    asyncio.run(main(args.host, args.port, args.audio_in))
    
    # 确保只打印最终的、纯净的文本结果
    print(final_result, end='')