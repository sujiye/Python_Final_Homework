"""
处理笔记数据,复制data文件夹到note文件夹,并根据条件筛选图片和文本
调用:process_notes_data(<source_data_dir>, <target_note_dir>)
参数:
    source_data_dir: 包含原始数据的文件夹路径,默认值为"data"
    target_note_dir: 目标笔记文件夹路径,默认值为"note"
输出:
    在target_note_dir文件夹中生成筛选后的笔记文件夹,每个文件夹包含符合条件的图片和文本文件
"""
import os
import shutil
import cv2

def process_notes_data(source_data_dir="data", target_note_dir="note"):
    print(f"start processing notes data from {source_data_dir} to {target_note_dir}")
    
    # 1. 复制 data 文件夹并重命名为 note
    if os.path.exists(target_note_dir):
        print(f"Target directory '{target_note_dir}' already exists, deleting it...")
        shutil.rmtree(target_note_dir)
    
    if os.path.exists(source_data_dir):
        print(f"Copying '{source_data_dir}' to '{target_note_dir}'...")
        shutil.copytree(source_data_dir, target_note_dir)
        print("Copy completed.")
    else:
        print(f"Failed to find source directory '{source_data_dir}'. Please ensure the scraped data has been generated.")
        return

    # 2. 遍历 note 文件夹及其子文件夹进行筛选
    print(f"Start filtering notes in '{target_note_dir}'...")
    for note_folder_name in os.listdir(target_note_dir):
        note_folder_path = os.path.join(target_note_dir, note_folder_name)

        if os.path.isdir(note_folder_path):
            print(f"\nProcessing note folder: {note_folder_name}")
            
            # 2.1. 图片分辨率筛选
            images_to_keep = []
            image_files = [f for f in os.listdir(note_folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            
            if not image_files:
                print(f"  Warning: No image files found in note folder '{note_folder_name}'.")
                # 如果没有图片，后续文本检查也可能导致删除，这里先不删除
            
            for image_file in image_files:
                image_path = os.path.join(note_folder_path, image_file)
                try:
                    img = cv2.imread(image_path)
                    if img is not None:
                        height, width, _ = img.shape
                        if width >= 500 and height >= 500:
                            images_to_keep.append(image_path)
                            print(f"  Image '{image_file}' resolution {width}x{height} meets the requirement.")
                        else:
                            os.remove(image_path)
                            print(f"  Image '{image_file}' resolution {width}x{height} does not meet the requirement (less than 500x500), deleted.")
                    else:
                        print(f"  Warning: Failed to read image file '{image_file}', may be corrupted.")
                        os.remove(image_path) # 删除无法读取的图片
                except Exception as e:
                    print(f"  Failed to process image '{image_file}' when reading: {e}，deleted.")
                    if os.path.exists(image_path):
                        os.remove(image_path)

            # 2.2. 文本内容筛选
            text_file_path = os.path.join(note_folder_path, "text.txt")
            text_content = ""
            if os.path.exists(text_file_path):
                try:
                    with open(text_file_path, 'r', encoding='utf-8') as f:
                        text_content = f.read().strip()
                    print(f"  Read text file '{text_file_path}' with content length: {len(text_content)}.")
                except Exception as e:
                    print(f"  Failed to read text file '{text_file_path}' when processing: {e}")
            else:
                print(f"  Warning: No 'text.txt' file found in note folder '{note_folder_name}'.")

            # 判断是否删除整个笔记文件夹
            # 删除条件：
            # 1. 没有符合分辨率的图片
            # 2. text.txt 不存在 或 内容少于10个字符
            
            should_delete_folder = False
            if not images_to_keep:
                print(f"  Note folder '{note_folder_name}' does not contain any images meeting the resolution requirement.")
                should_delete_folder = True
            
            if not text_content or len(text_content) < 10:
                print(f"  Note folder '{note_folder_name}' has empty or less than 10 characters of text content.")
                should_delete_folder = True

            if should_delete_folder:
                print(f"  Note folder '{note_folder_name}' does not meet the filtering criteria, deleting the entire folder...")
                shutil.rmtree(note_folder_path)
                print(f"  Deleted folder: {note_folder_name}")
            else:
                print(f"  Note folder '{note_folder_name}' meets the filtering criteria, kept.")

    print("\nNotes data processing completed.")

if __name__ == "__main__":
    process_notes_data()
