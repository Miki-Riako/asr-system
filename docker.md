## 本地部署Docker

通过该方法不用调用API，直接在本地部署。
```bash
sudo docker rm -f 055c5f54c1b13cf0f5eea0c23a5a53f650c656cc2a6e159da3620ec1b3de580a
# 或使用容器名
sudo docker rm -f funasr_server
```

### docker build

首先需要有docker

第二步：拉取 FunASR 并且启动离线服务镜像

现在您已经在容器内部了，这里是一个纯净且配置好的环境。请在容器的命令行中执行以下命令来启动后端的识别服务：

```bash
sudo docker pull registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-cpu-0.4.5
```

第三步：启动 FunASR 服务端容器
当镜像下载完成后，我们就可以用它启动一个服务容器了。请在您的 Paraformer-ASR 目录下（或者任何您方便的地方）运行以下命令：

```bash
# 这个命令会先创建一个本地目录，用于存放将来从网上下载的模型
mkdir -p ./funasr-runtime-resources/models

# 启动容器，并将我们刚创建的目录映射到容器内部
sudo docker run --name funasr_server -p 10095:10095 -it --privileged=true \
  -v $PWD/funasr-runtime-resources/models:/workspace/models \
  registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-cpu-0.4.5

```

当您运行这个命令后，您的终端会进入到 Docker 容器的内部，您会看到一个新的命令行提示符，类似 root@xxxxxx:/workspace#。

第四步：在容器内启动识别服务
现在您已经在容器内部了，这里是一个纯净且配置好的环境。请在容器的命令行中执行以下命令来启动后端的识别服务：

```bash
# 进入正确的目录
cd FunASR/runtime

# 启动服务脚本，它会自动下载所需的模型到 /workspace/models 目录
nohup bash run_server.sh \
  --download-model-dir /workspace/models \
  --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx \
  --model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-onnx  \
  --punc-dir damo/punc_ct-transformer_cn-en-common-vocab471067-large-onnx \
  --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst \
  --itn-dir thuduj12/fst_itn_zh \
  --hotword /workspace/models/hotwords.txt > log.txt 2>&1 &
```

服务会在后台启动。您可以运行 tail -f log.txt 来查看模型的下载和加载过程。当您看到类似 "Started server on 0.0.0.0:10095" 的日志时，就代表服务端已经准备就绪了。

下一步：确认服务状态（在当前容器终端）

为了确保服务已经完全准备就绪，您可以在当前这个容器的终端 (root@dca31...) 里，输入下面的命令查看日志：
```bash
tail -f log.txt
```

这个命令会持续显示日志的最新内容。请观察一下，当您看到类似 Started server on 0.0.0.0:10095 或者模型加载完成的日志时，就说明服务端已经准备好接收请求了。
确认完毕后，您可以按 Ctrl + C 退出日志查看，但请不要关闭这个终端窗口，让服务继续在后台运行。

### docker run

之后，再进入docker可以使用：

如果容器正在运行 (Up): 这是最理想的情况！说明您的识别服务还在后台运行。您只需要用 exec 命令在容器里打开一个新的终端窗口即可“进入”：
```bash
sudo docker exec -it funasr_server /bin/bash
```
执行后，您就会立刻回到熟悉的 root@... 命令行界面。
如果容器已经停止 (Exited): 这说明您可能关闭了它。没关系，我们分两步走：先启动它，再进入它。
```bash
# 第一步：重启容器
sudo docker start funasr_server

# 第二步：进入容器
sudo docker exec -it funasr_server /bin/bash
```
