import os
import whisper
import torch
import librosa
import soundfile as sf
from typing import List, Dict, Optional
import logging
from datetime import datetime
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ASREngine:
    def __init__(self, model_size: str = None):
        """
        初始化ASR引擎
        
        Args:
            model_size: Whisper模型大小 ("tiny", "base", "small", "medium", "large")
                       如果为None，则使用配置文件中的设置
        """
        self.model = None
        self.model_size = model_size or settings.ASR_MODEL_SIZE
        self.language = settings.ASR_LANGUAGE
        self.enable_gpu = settings.ASR_ENABLE_GPU
        self.processing_timeout = settings.ASR_PROCESSING_TIMEOUT
        self.initialized = False
        
    def initialize(self):
        """初始化ASR模型"""
        try:
            # 检查设备设置
            if self.enable_gpu and torch.cuda.is_available():
                device = "cuda"
                logger.info(f"使用GPU设备: {torch.cuda.get_device_name()}")
            else:
                device = "cpu"
                if self.enable_gpu:
                    logger.warning("GPU已启用但CUDA不可用，回退到CPU")
                logger.info("使用CPU设备")
            
            # 加载Whisper模型
            logger.info(f"正在加载Whisper {self.model_size}模型...")
            self.model = whisper.load_model(self.model_size, device=device)
            
            self.initialized = True
            logger.info(f"ASR引擎初始化成功 (模型: {self.model_size}, 设备: {device})")
            
        except Exception as e:
            logger.error(f"ASR引擎初始化失败: {str(e)}")
            self.initialized = False
            raise
    
    def transcribe_audio(self, audio_file_path: str, language: str = "zh") -> Dict:
        """
        转写音频文件
        
        Args:
            audio_file_path: 音频文件路径
            language: 语言代码 (默认为中文)
            
        Returns:
            包含转写结果的字典
        """
        if not self.initialized:
            self.initialize()
            
        if not self.initialized:
            raise RuntimeError("ASR引擎未能正确初始化")
            
        try:
            # 检查文件是否存在
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")
            
            logger.info(f"开始转写音频文件: {audio_file_path}")
            
            # 使用Whisper进行转写
            result = self.model.transcribe(
                audio_file_path,
                language=language,
                word_timestamps=True,
                verbose=False
            )
            
            # 转换结果格式
            formatted_result = self._format_transcription_result(result)
            
            logger.info(f"音频转写完成，生成了 {len(formatted_result['segments'])} 个分段")
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"音频转写失败: {str(e)}")
            raise
    
    def _format_transcription_result(self, whisper_result: Dict) -> Dict:
        """
        格式化Whisper的转写结果为统一格式
        
        Args:
            whisper_result: Whisper原始结果
            
        Returns:
            格式化后的结果
        """
        segments = []
        
        # 处理segments
        for i, segment in enumerate(whisper_result.get("segments", [])):
            # 提取基本信息
            segment_data = {
                "segment_id": i,
                "start_time": round(segment.get("start", 0), 2),
                "end_time": round(segment.get("end", 0), 2),
                "text": segment.get("text", "").strip(),
                "confidence": self._calculate_confidence(segment)
            }
            
            # 如果有词级别的时间戳，添加更详细的信息
            if "words" in segment:
                segment_data["words"] = [
                    {
                        "word": word.get("word", "").strip(),
                        "start": round(word.get("start", 0), 2),
                        "end": round(word.get("end", 0), 2),
                        "probability": word.get("probability", 0.5)
                    }
                    for word in segment["words"]
                ]
            
            segments.append(segment_data)
        
        return {
            "text": whisper_result.get("text", "").strip(),
            "language": whisper_result.get("language", "unknown"),
            "segments": segments,
            "duration": self._get_audio_duration(segments),
            "processing_time": datetime.now().isoformat()
        }
    
    def _calculate_confidence(self, segment: Dict) -> float:
        """
        计算分段的置信度
        
        Args:
            segment: Whisper分段数据
            
        Returns:
            置信度分数 (0.0-1.0)
        """
        # 如果有词级别的概率信息，计算平均值
        if "words" in segment and segment["words"]:
            probabilities = [word.get("probability", 0.5) for word in segment["words"]]
            return round(sum(probabilities) / len(probabilities), 3)
        
        # 否则使用默认置信度估算
        # 基于分段长度和其他启发式规则
        text_length = len(segment.get("text", "").strip())
        duration = segment.get("end", 0) - segment.get("start", 0)
        
        # 简单的置信度估算
        if text_length == 0:
            return 0.0
        elif duration <= 0:
            return 0.5
        else:
            # 基于语速的置信度估算 (合理语速约为2-6字符/秒)
            speech_rate = text_length / duration
            if 1 <= speech_rate <= 8:
                return min(0.95, 0.6 + (speech_rate / 20))
            else:
                return 0.4
    
    def _get_audio_duration(self, segments: List[Dict]) -> float:
        """获取音频总时长"""
        if not segments:
            return 0.0
        return max(segment["end_time"] for segment in segments)
    
    def preprocess_audio(self, input_path: str, output_path: str = None) -> str:
        """
        预处理音频文件（格式转换、降噪等）
        
        Args:
            input_path: 输入音频文件路径
            output_path: 输出文件路径（可选）
            
        Returns:
            处理后的音频文件路径
        """
        try:
            # 如果没有指定输出路径，创建临时文件
            if output_path is None:
                import tempfile
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, f"{base_name}_processed.wav")
            
            # 使用librosa加载和重采样音频
            audio, original_sr = librosa.load(input_path, sr=None)
            
            # 重采样到16kHz（Whisper的标准采样率）
            target_sr = 16000
            if original_sr != target_sr:
                audio = librosa.resample(audio, orig_sr=original_sr, target_sr=target_sr)
            
            # 保存处理后的音频
            sf.write(output_path, audio, target_sr)
            
            logger.info(f"音频预处理完成: {input_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"音频预处理失败: {str(e)}")
            raise
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的音频格式"""
        return settings.ASR_SUPPORTED_FORMATS
    
    def validate_audio_file(self, file_path: str) -> bool:
        """验证音频文件是否有效"""
        try:
            # 检查文件扩展名
            _, ext = os.path.splitext(file_path.lower())
            if ext not in self.get_supported_formats():
                return False
            
            # 尝试加载音频文件的元数据
            duration = librosa.get_duration(path=file_path)
            return duration > 0
            
        except Exception:
            return False

# 全局ASR引擎实例
asr_engine = ASREngine()

def get_asr_engine() -> ASREngine:
    """获取ASR引擎实例"""
    return asr_engine 