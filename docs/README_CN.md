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
<a href="https://opensource.org/license/apache-2-0"><img src="https://img.shields.io/badge/License-apache2-yellow.svg" alt="License: MIT"></a>
</p>

AutoAgents是一个基于LLM的自动代理生成实验的实验性开源应用程序。该程序由LLM驱动，自主生成多智能体以实现您设定的任何目标。

<p align="center">
    <img src=./resources/framework.jpg width="800">
</p>

## 🚀 特点
-**Planner**：根据问题确定要添加的专家角色和具体的执行计划。
-**工具**：可使用的工具集，目前仅支持搜索工具。
-**观察员**：负责反思执行过程中的计划和结果是否合理，目前包括对智能体、计划和行动的反思检查。
-**信史**：负责代理人之间的信息交流，协调多个代理人的执行顺序。
-**智能体**：生成的专家角色智能体，包括名称、专业知识、使用的工具和LLM模型。
-**计划**：执行计划由生成的专家角色组成，执行计划的每个步骤至少有一个专家角色代理。
-**动作**：执行计划中专家角色的具体动作，如调用工具或输出结果。

## 演示
TODO

## 安装与使用

### 传统安装

```bash
# Step 1: Ensure that NPM is installed on your system. Then install mermaid-js.
npm --version
sudo npm install -g @mermaid-js/mermaid-cli

# Step 2: Ensure that Python 3.9+ is installed on your system. You can check this by using:
python --version

# Step 3: Clone the repository to your local machine, and install it.
git clone https://github.com/iCGY96/autoagents
cd autoagents
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
```python
python startup.py "Write a cli snake game"
```

## 联系信息

如果您对这个项目有任何问题或反馈，欢迎联系我们。我们非常欢迎您的建议！

- **邮箱:** gy.chen@foxmail.com, ymshi@linksoul.ai
- **GitHub 问题:**  对于更技术性的问题，您也可以在我们的 [GitHub repository](https://github.com/iCGY96/autoagents/issues)中创建一个新的问题。

我们会在2-3个工作日内回复所有问题。
