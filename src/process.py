import os
import shutil
import cv2

def process_notes_data(source_data_dir="data", target_note_dir="note"):
    print(f"开始处理笔记数据，源目录：{source_data_dir}，目标目录：{target_note_dir}")
    
    # 1. 复制 data 文件夹并重命名为 note
    if os.path.exists(target_note_dir):
        print(f"目标目录 '{target_note_dir}' 已存在，正在删除旧目录...")
        shutil.rmtree(target_note_dir)
    
    if os.path.exists(source_data_dir):
        print(f"正在复制 '{source_data_dir}' 到 '{target_note_dir}'...")
        shutil.copytree(source_data_dir, target_note_dir)
        print("复制完成。")
    else:
        print(f"错误：源目录 '{source_data_dir}' 不存在。请确保爬取数据已生成。")
        return

    # 2. 遍历 note 文件夹及其子文件夹进行筛选
    print(f"开始筛选 '{target_note_dir}' 目录下的笔记...")
    for note_folder_name in os.listdir(target_note_dir):
        note_folder_path = os.path.join(target_note_dir, note_folder_name)

        if os.path.isdir(note_folder_path):
            print(f"\n正在处理笔记文件夹：{note_folder_name}")
            
            # 2.1. 图片分辨率筛选
            images_to_keep = []
            image_files = [f for f in os.listdir(note_folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            
            if not image_files:
                print(f"  警告：笔记文件夹 '{note_folder_name}' 中没有图片文件。")
                # 如果没有图片，后续文本检查也可能导致删除，这里先不删除
            
            for image_file in image_files:
                image_path = os.path.join(note_folder_path, image_file)
                try:
                    img = cv2.imread(image_path)
                    if img is not None:
                        height, width, _ = img.shape
                        if width >= 500 and height >= 500:
                            images_to_keep.append(image_path)
                            print(f"  图片 '{image_file}' 分辨率 {width}x{height} 符合要求。")
                        else:
                            os.remove(image_path)
                            print(f"  图片 '{image_file}' 分辨率 {width}x{height} 不符合要求 (小于500x500)，已删除。")
                    else:
                        print(f"  警告：无法读取图片文件 '{image_file}'，可能已损坏。")
                        os.remove(image_path) # 删除无法读取的图片
                except Exception as e:
                    print(f"  处理图片 '{image_file}' 时发生错误：{e}，已删除。")
                    if os.path.exists(image_path):
                        os.remove(image_path)

            # 2.2. 文本内容筛选
            text_file_path = os.path.join(note_folder_path, "text.txt")
            text_content = ""
            if os.path.exists(text_file_path):
                try:
                    with open(text_file_path, 'r', encoding='utf-8') as f:
                        text_content = f.read().strip()
                    print(f"  读取到文本文件 '{text_file_path}'，内容长度：{len(text_content)}。")
                except Exception as e:
                    print(f"  读取文本文件 '{text_file_path}' 时发生错误：{e}")
            else:
                print(f"  警告：笔记文件夹 '{note_folder_name}' 中未找到 'text.txt' 文件。")

            # 判断是否删除整个笔记文件夹
            # 删除条件：
            # 1. 没有符合分辨率的图片
            # 2. text.txt 不存在 或 内容少于10个字符
            
            should_delete_folder = False
            if not images_to_keep:
                print(f"  笔记文件夹 '{note_folder_name}' 中没有符合分辨率要求的图片。")
                should_delete_folder = True
            
            if not text_content or len(text_content) < 10:
                print(f"  笔记文件夹 '{note_folder_name}' 的文本内容为空或少于10个字符。")
                should_delete_folder = True

            if should_delete_folder:
                print(f"  笔记文件夹 '{note_folder_name}' 不符合筛选条件，正在删除整个文件夹...")
                shutil.rmtree(note_folder_path)
                print(f"  已删除文件夹：{note_folder_name}")
            else:
                print(f"  笔记文件夹 '{note_folder_name}' 符合筛选条件，保留。")

    print("\n笔记数据处理完成。")

if __name__ == "__main__":
    process_notes_data()
