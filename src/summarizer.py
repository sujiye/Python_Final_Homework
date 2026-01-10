"""
利用智谱AI API进行文本总结
调用:summarizer.summarize_notes(<note_folder_path>, <output_file_path>, <api_key>)
参数:
    note_folder_path: 包含待总结文本文件的文件夹路径
    output_file_path: 总结结果输出的文件路径
    api_key: 智谱AI API密钥
输出:
    结果写入指定的输出文件路径
"""
import os
from zai import ZhipuAiClient

class ZhipuAI:
    def __init__(self, apikey):
        self.client = ZhipuAiClient(api_key=apikey)
        self.messages = [
            {
                "role": "system",
                "content": self._read_prompt_from_file("./prompts.txt")
            }
        ]
        self.thinking = {"type":"enable"}
        self.model = "glm-4.5-flash"
        self.temperature = 0.6
        self.stream = True

    def _read_prompt_from_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Failed to find prompt file: {file_path}")
            return "你是一个有用的AI助手。"
        except Exception as e:
            print(f"Failed to read prompt file {file_path}: {e}")
            return "你是一个有用的AI助手。"

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})

    def get_response(self):
        response_generator = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
            thinking=self.thinking,
            stream=True
        )
        full_response_content = ""
        for chunk in response_generator:
            if chunk.choices[0].delta.content:
                full_response_content += chunk.choices[0].delta.content
        self.add_message("assistant", full_response_content)
        return full_response_content

def summarize_notes(note_folder_path, output_file_path, api_key):
    """
    总结指定文件夹内的所有文本文件，并将总结结果写入输出文件。
    """
    zhipuai = ZhipuAI(api_key)
    all_summaries = []

    for root, _, files in os.walk(note_folder_path):
        for file_name in files:
            if file_name.endswith(".txt"):
                file_path = os.path.join(root, file_name)
                print(f"summarizing: {file_path}")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # 清空之前的消息，只保留系统消息
                    zhipuai.messages = [zhipuai.messages[0]]
                    zhipuai.add_message("user", f"请总结以下文本内容：\n{content}")
                    summary = zhipuai.get_response()
                    all_summaries.append(f"--- 文件: {file_name} ---\n{summary}\n")
                except Exception as e:
                    all_summaries.append(f"--- 文件: {file_name} (错误) ---\n总结失败: {e}\n")
                    print(f"Failed to summarize {file_name}: {e}")

    with open(output_file_path, "w", encoding="utf-8") as outfile:
        for summary in all_summaries:
            outfile.write(summary)
    print(f"All summaries have been written to: {output_file_path}")

if __name__ == "__main__":
    api_key = "f7d63519cd5942f0a5907e76346aa1bf.GEzosOeBYThSxlsk" # 智谱AI API密钥
    note_folder = "./note" # note文件夹路径
    output_summary_file = "./note/summaries.txt" # 总结输出文件路径

    summarize_notes(note_folder, output_summary_file, api_key)
