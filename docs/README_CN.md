# AutoAgents：多智能体自动生成框架

<p align="center">
<a href=""><img src="resources/logo-autoagents.jpg" alt="autoagents logo: Enable GPT to work in software company, collaborating to tackle more complex tasks." width="150px"></a>
</p>

<p align="center">
<b>为GPT生成不同的角色，通过多智能体处理更复杂的任务。
</b>
</p>

<p align="center">
<a href="docs/README_CN.md"><img src="https://img.shields.io/badge/文档-中文版-blue.svg" alt="CN doc"></a>
<a href="README.md"><img src="https://img.shields.io/badge/document-English-blue.svg" alt="EN doc"></a>
<a href="./README_JA.md"><img src="https://img.shields.io/badge/ドキュメント-日本語-blue.svg" alt="JA doc"></a>
<a href="https://opensource.org/license/apache-2-0"><img src="https://img.shields.io/badge/License-apache2-yellow.svg" alt="License: MIT"></a>
</p>

AutoAgents是一个基于LLM的自动代理生成实验的实验性开源应用程序。该程序由LLM驱动，自主生成多智能体以实现您设定的任何目标。

<p align="center">
    <img src=./resources/framework2.jpg width="800">
</p>

## 🚀 特点
- **Planner**：根据问题确定要添加的专家角色和具体的执行计划。
- **工具**：可使用的工具集，目前仅支持搜索工具。
- **观察员**：负责反思执行过程中的计划和结果是否合理，目前包括对智能体、计划和行动的反思检查。
- **智能体**：生成的专家角色智能体，包括名称、专业知识、使用的工具和LLM模型。
- **计划**：执行计划由生成的专家角色组成，执行计划的每个步骤至少有一个专家角色代理。
- **动作**：执行计划中专家角色的具体动作，如调用工具或输出结果。

## 演示
在线演示： 
- [DEMO / HuggingFace Spaces](https://huggingface.co/spaces/LinkSoul/AutoAgents)

视频演示：
- **谣言验证**
<video src='https://github.com/shiyemin/AutoAgents/assets/1501158/41898e0d-4137-450c-ad9b-bfb9b8c1d27b.mp4'></video>
- **贪吃蛇游戏**
<video src='https://github.com/shiyemin/AutoAgents/assets/1501158/a327dbcc-4b7f-45f8-81ce-6eafd8071df1.mp4'></video>

## 安装与使用

### 传统安装

```bash
git clone https://github.com/LinkSoul-AI/AutoAgents
cd AutoAgents
python setup.py install
```

### 配置

- 在`config/key.yaml / config/config.yaml / env`中配置您的`OPENAI_API_KEY`。 
- 优先级顺序：`config/key.yaml > config/config.yaml > env`

```bash
# Copy the configuration file and make the necessary modifications.
cp config/config.yaml config/key.yaml
```

| 变量名                             | config/key.yaml                           | env                                             |
| ------------------------------------------ | ----------------------------------------- | ----------------------------------------------- |
| OPENAI_API_KEY # 用您自己的密钥替换 | OPENAI_API_KEY: "sk-..."                  | export OPENAI_API_KEY="sk-..."                  |
| OPENAI_API_BASE # 可选                 | OPENAI_API_BASE: "https://<YOUR_SITE>/v1" | export OPENAI_API_BASE="https://<YOUR_SITE>/v1" |

### 使用
- 命令行模式:
```python
python main.py --mode commandline --llm_api_key YOUR_OPENAI_API_KEY --serapi_key YOUR_SERPAPI_KEY --idea "Is LK-99 really a room temperature superconducting material?"
```
- Websocket服务模式:
```python
python main.py --mode service --host "127.0.0.1" --port 9000
```
### Docker
- 生成docker镜像:
```bash
IMAGE="linksoul.ai/autoagents"
VERSION=1.0

docker build -f docker/Dockerfile -t "${IMAGE}:${VERSION}" .
```
- 启动docker容器:
```bash
docker run -it --rm -p 7860:7860 "${IMAGE}:${VERSION}"
```
- 用浏览器打开：http://127.0.0.1:7860


## 联系信息

如果您对这个项目有任何问题或反馈，欢迎联系我们。我们非常欢迎您的建议！

- **邮箱:** gy.chen@foxmail.com, ymshi@linksoul.ai
- **GitHub 问题:**  对于更技术性的问题，您也可以在我们的 [GitHub repository](https://github.com/LinkSoul-AI/AutoAgents/issues)中创建一个新的问题。

我们会在2-3个工作日内回复所有问题。

## 致谢
AutoAgents 遵守 MIT 协议开源，其中项目的虚拟环境部分基于同样使用 MIT 协议的开源项目 [MetaGPT](https://github.com/geekan/MetaGPT) 实现。
