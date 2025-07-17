from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import subprocess
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/asr",
    tags=["transcription"]
)

@router.post("/transcribe/file")
async def transcribe_file(file: UploadFile = File(...)):
    """
    上传音频文件并返回转写结果
    """
    try:
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        root_dir = os.path.dirname(current_dir)  # 回到asr-system目录
        
        logger.info(f"Processing file: {file.filename}")
        
        # 临时文件路径
        file_path = os.path.join(root_dir, "client", f"temp_{file.filename}")
        temp_script = os.path.join(root_dir, "client", "temp_test.sh")
        
        # 保存上传的文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        logger.info(f"Saved file to: {file_path}")
        
        # 修改test_demo.sh中的音频文件路径
        demo_script = os.path.join(root_dir, "client", "test_demo.sh")
        with open(demo_script, "r") as f:
            script_content = f.read()
        
        # 替换音频文件路径
        script_content = script_content.replace("BAC009S0764W0179.wav", f"temp_{file.filename}")
        
        # 保存临时脚本
        with open(temp_script, "w") as f:
            f.write(script_content)
        
        # 设置脚本可执行权限
        os.chmod(temp_script, 0o755)
        logger.info("Created and configured temporary script")
        
        # 执行脚本
        os.chdir(root_dir)  # 切换到项目根目录
        logger.info(f"Executing script from directory: {root_dir}")
        result = subprocess.run([f"./client/temp_test.sh"], shell=True, capture_output=True, text=True)
        output = result.stdout + result.stderr
        logger.info("Script execution completed")
        
        # 解析结果
        transcription = ""
        for line in output.split("\n"):
            if "pid0_0: demo:" in line:
                transcription = line.split("pid0_0: demo:")[-1].strip()
                logger.info(f"Found transcription: {transcription}")
                break
        
        if not transcription:
            logger.warning("No transcription found in output")
            logger.debug(f"Full output: {output}")
            
        return {
            "result": transcription
        }
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(temp_script):
            os.remove(temp_script)
        logger.info("Cleaned up temporary files") 