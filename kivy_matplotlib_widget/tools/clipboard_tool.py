"""
Tool to copy a widget to clipboard

manage windows, linux (via xclip) and MacOS platform

not functionnal with Android platform
(need to do something similar as kivy\core\clipboard\clipboard_android.py)

Note: A new image clipboard is be planned in kivy 3.0.0
https://github.com/kivy/kivy/issues/8631

So this tool will certaintly be removed or modified in the futur
"""

from io import BytesIO

from kivy.utils import platform
from PIL import Image as PILImage

if platform == 'win':
    import win32clipboard
elif platform == 'linux':
    """
    used xclip to copy to clipboard
    """
    import subprocess
    import tempfile

elif platform == 'macosx':
    """
    Appkit come with pyobjc
    """
    from AppKit import NSPasteboard, NSPasteboardTypePNG
    from Foundation import NSData


def image2clipboard(widget):

    if platform == 'win':
        def send_to_clipboard(clip_type, data):
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(clip_type, data)
            win32clipboard.CloseClipboard()

        img = widget.export_as_image() #export widget as image
        pil_img = PILImage.frombytes('RGBA',
                                     img.texture.size,
                                     img.texture.pixels)

        output = BytesIO()
        pil_img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        send_to_clipboard(win32clipboard.CF_DIB, data)

    elif platform == 'linux':

        def _copy_linux_xclip(image):
            """On Linux, copy the `image` to the clipboard. The `image` arg can either be
            a PIL.Image.Image object or a str/Path refering to an image file.
            """

            with tempfile.NamedTemporaryFile() as temp_file_obj:
                image.save(temp_file_obj.name, format='png')
                subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-i', temp_file_obj.name])

        img = widget.export_as_image() #export widget as image
        pil_img = PILImage.frombytes('RGBA',
                                    img.texture.size,
                                    img.texture.pixels)
        _copy_linux_xclip(pil_img)

    elif platform == 'macosx':
        img = widget.export_as_image() #export widget as image
        pil_img = PILImage.frombytes('RGBA',
                                     img.texture.size,
                                     img.texture.pixels)
        output = BytesIO()
        pil_img.save(output, format="PNG")
        data = output.getvalue()
        output.close()

        image_data  = NSData.dataWithBytes_length_(data, len(data))

        pasteboard = NSPasteboard.generalPasteboard()
        format_type = NSPasteboardTypePNG
        pasteboard.clearContents()
        pasteboard.setData_forType_(image_data, format_type)