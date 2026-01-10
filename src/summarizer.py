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
    all_text_contents = []

    for root, _, files in os.walk(note_folder_path):
        for file_name in files:
            if file_name.endswith(".txt"):
                file_path = os.path.join(root, file_name)
                print(f"reading file: {file_path}")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        all_text_contents.append(content)
                except Exception as e:
                    print(f"Failed to read file {file_name}: {e}")
    
    combined_text = "\n\n".join(all_text_contents)
    if not combined_text:
        print("No text content found to summarize.")
        return

    print("Summarizing all collected text content...")
    # 清空之前的消息，只保留系统消息
    zhipuai.messages = [zhipuai.messages[0]]
    zhipuai.add_message("user", f"请总结以下所有文本内容：\n{combined_text}")
    final_summary = zhipuai.get_response()

    with open(output_file_path, "w", encoding="utf-8") as outfile:
        outfile.write(final_summary)
    print(f"All collected text content has been summarized and written to: {output_file_path}")

if __name__ == "__main__":
    api_key = "f7d63519cd5942f0a5907e76346aa1bf.GEzosOeBYThSxlsk" # 智谱AI API密钥
    note_folder = "./note" # note文件夹路径
    output_summary_file = "./note/summaries.txt" # 总结输出文件路径

    summarize_notes(note_folder, output_summary_file, api_key)
