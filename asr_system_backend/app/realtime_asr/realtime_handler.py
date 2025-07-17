import numpy as np
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import io
import wave
from typing import Optional
import asyncio
import soundfile as sf
import tempfile
import subprocess
import os

class RealtimeASRHandler:
    def __init__(self):
        # 初始化Whisper模型
        self.processor = WhisperProcessor.from_pretrained("openai/whisper-small")
        self.model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")
        if torch.cuda.is_available():
            self.model = self.model.to("cuda")
        
        # 音频缓冲设置
        self.sample_rate = 16000  # Whisper期望的采样率
        self.audio_buffer = np.array([], dtype=np.float32)
        self.buffer_size = self.sample_rate * 3  # 3秒的音频缓冲
        
        # 转写设置
        self.is_processing = False
        self.last_transcription = ""

    async def process_audio(self, audio_data: bytes) -> Optional[str]:
        try:
            # 将webm音频数据转换为numpy数组
            audio_array = await self._convert_webm_to_array(audio_data)
            if audio_array is None:
                return None
            
            # 添加到缓冲区
            self.audio_buffer = np.append(self.audio_buffer, audio_array)
            
            # 如果缓冲区达到指定大小，进行处理
            if len(self.audio_buffer) >= self.buffer_size and not self.is_processing:
                self.is_processing = True
                try:
                    # 处理音频并获取转写结果
                    transcription = await self._transcribe_audio()
                    self.last_transcription = transcription
                    
                    # 清除已处理的音频数据，保留最后0.5秒以实现平滑过渡
                    overlap_samples = int(0.5 * self.sample_rate)
                    self.audio_buffer = self.audio_buffer[-overlap_samples:]
                    
                finally:
                    self.is_processing = False
                
                return self.last_transcription
            
            return None
            
        except Exception as e:
            print(f"处理音频时出错: {str(e)}")
            return None

    async def _convert_webm_to_array(self, audio_data: bytes) -> Optional[np.ndarray]:
        try:
            # 创建临时文件来存储音频数据
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as webm_file:
                webm_file.write(audio_data)
                webm_path = webm_file.name

            # 创建临时WAV文件
            wav_path = webm_path + '.wav'
            
            # 使用ffmpeg将webm转换为wav
            cmd = [
                'ffmpeg',
                '-i', webm_path,
                '-ar', str(self.sample_rate),
                '-ac', '1',
                '-f', 'wav',
                wav_path,
                '-y'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode == 0:
                # 读取转换后的WAV文件
                audio_array, _ = sf.read(wav_path)
                return audio_array.astype(np.float32)
            else:
                print("音频转换失败")
                return None
                
        except Exception as e:
            print(f"转换音频格式时出错: {str(e)}")
            return None
            
        finally:
            # 清理临时文件
            try:
                os.unlink(webm_path)
                os.unlink(wav_path)
            except:
                pass

    async def _transcribe_audio(self) -> str:
        # 在事件循环中运行转写任务
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run_transcription)

    def _run_transcription(self) -> str:
        try:
            # 准备输入特征
            input_features = self.processor(
                self.audio_buffer, 
                sampling_rate=self.sample_rate, 
                return_tensors="pt"
            ).input_features
            
            if torch.cuda.is_available():
                input_features = input_features.to("cuda")
            
            # 生成转写
            predicted_ids = self.model.generate(input_features)
            transcription = self.processor.batch_decode(
                predicted_ids, 
                skip_special_tokens=True
            )[0]
            
            return transcription.strip()
        except Exception as e:
            print(f"转写过程出错: {str(e)}")
            return ""

    async def cleanup(self):
        # 清理资源
        self.audio_buffer = np.array([], dtype=np.float32)
        self.is_processing = False 