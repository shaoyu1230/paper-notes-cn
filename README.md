# Paper Notes CN

从 arXiv 论文筛选结果自动生成中文解读草稿，并将草稿存档到 Git 仓库，后续可接入自动发布流程（例如微信公众号）。

## 目录结构

- `data/`: 输入数据（arxiv 过滤结果）
- `drafts/`: 生成的中文解读草稿（Markdown）
- `prompts/`: 草稿生成模板与提示词
- `scripts/`: 脚本工具

## 快速开始

1) 准备筛选结果（来自上一步脚本）

```bash
cp /Users/angela/Documents/08_知识博主/arxiv_filtered.json /Users/angela/Documents/08_知识博主/paper-notes-cn/data/arxiv_filtered.json
```

2) 生成中文草稿（默认占位草稿，便于人工修改）

```bash
python3 /Users/angela/Documents/08_知识博主/paper-notes-cn/scripts/generate_drafts.py \
  --input-json /Users/angela/Documents/08_知识博主/paper-notes-cn/data/arxiv_filtered.json \
  --output-dir /Users/angela/Documents/08_知识博主/paper-notes-cn/drafts \
  --max-papers 10
```

3) 可选：接入任意本地或云端 LLM，自动生成更完整草稿

将 `LLM_COMMAND` 设置为一个命令行程序，它从 stdin 读取提示词并向 stdout 输出生成内容：

```bash
export LLM_COMMAND="python3 /path/to/your_llm_client.py"
python3 /Users/angela/Documents/08_知识博主/paper-notes-cn/scripts/generate_drafts.py \
  --input-json /Users/angela/Documents/08_知识博主/paper-notes-cn/data/arxiv_filtered.json \
  --output-dir /Users/angela/Documents/08_知识博主/paper-notes-cn/drafts \
  --max-papers 10 \
  --use-llm
```

4) 使用 OpenAI 直接生成中文草稿

```bash
pip install -r /Users/angela/Documents/08_知识博主/paper-notes-cn/requirements.txt
export OPENAI_API_KEY="YOUR_API_KEY"

python3 /Users/angela/Documents/08_知识博主/paper-notes-cn/scripts/generate_drafts.py \
  --input-json /Users/angela/Documents/08_知识博主/paper-notes-cn/data/arxiv_filtered.json \
  --output-dir /Users/angela/Documents/08_知识博主/paper-notes-cn/drafts \
  --max-papers 10 \
  --provider openai \
  --openai-model gpt-5
```

5) 使用通义千问（Qwen）直接生成中文草稿

```bash
pip install -r /Users/angela/Documents/08_知识博主/paper-notes-cn/requirements.txt
export DASHSCOPE_API_KEY="YOUR_API_KEY"

python3 /Users/angela/Documents/08_知识博主/paper-notes-cn/scripts/generate_drafts.py \
  --input-json /Users/angela/Documents/08_知识博主/paper-notes-cn/data/arxiv_filtered.json \
  --output-dir /Users/angela/Documents/08_知识博主/paper-notes-cn/drafts \
  --max-papers 10 \
  --provider qwen \
  --qwen-model qwen-plus \
  --qwen-base-url https://dashscope.aliyuncs.com/compatible-mode/v1
```

6) 使用 MiniMax（M2.5）直接生成中文草稿

```bash
pip install -r /Users/angela/Documents/08_知识博主/paper-notes-cn/requirements.txt
export MINIMAX_API_KEY="YOUR_API_KEY"

python3 /Users/angela/Documents/08_知识博主/paper-notes-cn/scripts/generate_drafts.py \
  --input-json /Users/angela/Documents/08_知识博主/paper-notes-cn/data/arxiv_filtered.json \
  --output-dir /Users/angela/Documents/08_知识博主/paper-notes-cn/drafts \
  --max-papers 10 \
  --provider minimax \
  --minimax-model MiniMax-M2.5 \
  --minimax-base-url https://api.hizui.cn/v1
```

7) 使用 Gemini 兼容接口（hizui）生成中文草稿

```bash
pip install -r /Users/angela/Documents/08_知识博主/paper-notes-cn/requirements.txt
export GEMINI_API_KEY="YOUR_API_KEY"

python3 /Users/angela/Documents/08_知识博主/paper-notes-cn/scripts/generate_drafts.py \
  --input-json /Users/angela/Documents/08_知识博主/paper-notes-cn/data/arxiv_filtered.json \
  --output-dir /Users/angela/Documents/08_知识博主/paper-notes-cn/drafts \
  --max-papers 10 \
  --provider gemini \
  --gemini-model MiniMax-M2.5 \
  --gemini-base-url https://api.hizui.cn
```

## 每日自动化

编辑配置文件：

```bash
open /Users/angela/Documents/08_知识博主/paper-notes-cn/data/config.json
```

运行每日流程（获取论文 -> 生成草稿 -> 提交推送）：

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
python3 /Users/angela/Documents/08_知识博主/paper-notes-cn/scripts/run_daily.py
```

## 草稿规范

草稿文件名格式：`YYYY-MM-DD_arXivID.md`  
草稿内容包含 Front Matter（元数据）和正文结构（可直接人工修改）。
