from tkinter import Tk, Label, Button, Listbox, SINGLE, END
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image
import os


def concatenate_images_vertically(image_paths, output_path):
    images = [Image.open(image_path) for image_path in image_paths]
    widths, heights = zip(*(i.size for i in images))
    total_width = max(widths)
    total_height = sum(heights)
    new_image = Image.new('RGB', (total_width, total_height))

    y_offset = 0
    for img in images:
        new_image.paste(img, (0, y_offset))
        y_offset += img.size[1]

    new_image.save(output_path)


def on_drop(event):
    files = root.tk.splitlist(event.data)
    image_paths = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
    if not image_paths:
        label.config(text="이미지 파일이 아닙니다.")
        return

    for path in image_paths:
        listbox.insert(END, path)


def move_up():
    sel = listbox.curselection()
    if not sel:
        return
    idx = sel[0]
    if idx == 0:
        return
    text = listbox.get(idx)
    listbox.delete(idx)
    listbox.insert(idx - 1, text)
    listbox.selection_set(idx - 1)


def move_down():
    sel = listbox.curselection()
    if not sel:
        return
    idx = sel[0]
    if idx == listbox.size() - 1:
        return
    text = listbox.get(idx)
    listbox.delete(idx)
    listbox.insert(idx + 1, text)
    listbox.selection_set(idx + 1)


def clear_list():
    listbox.delete(0, END)
    label.config(text="리스트가 비워졌습니다.")


def delete_selected(event=None):  # Delete 키와 버튼 둘 다 쓸 수 있게
    sel = listbox.curselection()
    if not sel:
        return
    listbox.delete(sel[0])
    label.config(text="선택한 항목이 삭제되었습니다.")


def combine_images():
    if listbox.size() == 0:
        label.config(text="리스트가 비어 있습니다.")
        return

    image_paths = [listbox.get(i) for i in range(listbox.size())]
    output_dir = os.path.dirname(image_paths[0])
    output_path = os.path.join(output_dir, "combined_image.jpg")

    concatenate_images_vertically(image_paths, output_path)
    label.config(text=f"이미지가 성공적으로 저장되었습니다: {output_path}")


# 메인 윈도우
root = TkinterDnD.Tk()
root.title("이미지 드래그 앤 드롭")

label = Label(root, text="이미지 파일을 드래그 앤 드롭하세요")
label.pack(pady=10)

listbox = Listbox(root, selectmode=SINGLE, width=80, height=10)
listbox.pack(pady=5)

# Delete 키 바인딩
listbox.bind("<Delete>", delete_selected)

# 버튼들
Button(root, text="위로", command=move_up).pack(pady=2)
Button(root, text="아래로", command=move_down).pack(pady=2)
Button(root, text="선택 삭제", command=delete_selected).pack(pady=2)  # 버튼도 같이
Button(root, text="리스트 비우기", command=clear_list).pack(pady=2)
Button(root, text="합치기", command=combine_images).pack(pady=10)

# 드래그 앤 드롭
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', on_drop)

root.mainloop()
