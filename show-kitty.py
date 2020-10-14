import json
import os
import pickle
import tkinter
import urllib.request
from html.parser import HTMLParser

query = "kitten"
directory = query


class Config():
    def __init__(self):
        self.page = 1
        self.start = 1


def load_config(prefix: str) -> Config:
    try:
        with open(prefix + "/config.dat", "rb") as config_file:
            conf = pickle.Unpickler(config_file).load()
    except FileNotFoundError:
        conf = Config()
    return conf


def save_config(config: Config, prefix: str):
    with open(prefix + "/config.dat", "wb") as config_file:
        pickle.Pickler(config_file).dump(config)


def get_vqd_from_duckduckgo():
    """
    Method reads validation query data (vqd) from response on first request from duckduckgo
    :return: string containing vqd value
    """

    class VqdHTMLParser(HTMLParser):
        """
        Class reads validation data from response on first request from duckduckgo
        :return:
        """
        _insideScriptTag = False
        _vqd = ''

        def handle_starttag(self, tag, attrs):
            if tag.startswith("script"):
                self._insideScriptTag = True

        def handle_data(self, data):
            if self._insideScriptTag:
                if data.startswith("var"):
                    definitions = data.split(';')
                    for definition in definitions:
                        if definition.startswith("vqd"):
                            self._vqd = definition.split('=')[1]
                            self._vqd = self._vqd.strip('\'')

        def handle_endtag(self, tag):
            if tag.startswith("script"):
                self._insideScriptTag = False

    vqd_parser = VqdHTMLParser()
    first_request = urllib.request.Request(
        r"https://duckduckgo.com/?q={}&t=h_&iaf=type%3Agif&iax=images&ia=images".format(query))
    with urllib.request.urlopen(first_request) as response:
        payload = response.read().decode("UTF-8")
        vqd_parser.feed(payload)
        vqd = vqd_parser._vqd
    return vqd


def get_image_from_duckduckgo(pics: list, vqd: str, config: Config):
    """
    Method reads image list from duckduckgo
    for proper request it need vqd, page of results and number of first image to show
    :return: string containing filename of image
    """
    get_img = "https://duckduckgo.com/i.js?" \
              "l=pl-pl&o=json&q={}&vqd={}&f=,type:gif,,&p={}&s={}".format(query, vqd, config.page, config.start)
    with urllib.request.urlopen(get_img) as response:
        payload = response.read().decode("UTF-8")
        obj = json.loads(payload)
        filename = ""
        for res in obj['results']:
            imagepath = res['image'].split('?')[0]
            print(" < {}".format(imagepath))
            filename = imagepath.split('/')[-1]
            print(" > {}".format(filename))
            config.start += 1
            if filename in pics or (not filename.endswith(".gif") and not filename.endswith(".giff")):
                continue
            try:
                urllib.request.urlretrieve(imagepath, query + '/' + filename)
            except:
                continue
            return filename


def get_images_from_directory(dir: str):
    """
    Method reads image list from directory where script is running
    :return: list of strings containing image-names
    """
    filenames = []
    try:
        filenames = filter(lambda fname: not fname.endswith('py') and not fname.endswith('dat'), os.listdir(dir))
    except FileNotFoundError:
        os.mkdir(dir)
    return filenames


def load_pic(filename):
    return tkinter.PhotoImage(file=filename, format="gif -index {}".format(0))

root = None
label = None
button_prev = None
button_next = None
pic_ind = 0
pics = []


def get_img():
    """
    Method performs whole scenario getting image from duckduckgo
    :return: string containing image-name
    """
    global pics, directory
    vqd = get_vqd_from_duckduckgo()
    config = load_config(directory)
    picname = get_image_from_duckduckgo(pics, vqd, config)
    save_config(config, directory)
    return picname


def on_back():
    global pic_ind, pics
    pic_ind -= 1
    if pic_ind <= 0:
        button_prev.configure(state=tkinter.DISABLED)
    change_pic(directory + "/" + pics[pic_ind])

    
def on_next():
    global pic_ind, pics, directory
    pic_ind += 1
    button_prev.configure(state=tkinter.ACTIVE)
    change_pic(directory + "/" + pics[pic_ind])
    label.update()
    if pic_ind >= len(pics) - 1:
        download_pic()


def download_pic():
    button_next.configure(text="Downloading...", state=tkinter.DISABLED)
    button_next.update()
    pics.append(get_img())
    button_next.configure(text="Next", state=tkinter.ACTIVE)
    button_next.update()


def change_pic(filename: str):
    global label
    img = load_pic(filename)
    label.configure(image=img)
    label.image = img


def init_gui():
    global button_prev, button_next, label, root
    root = tkinter.Tk()
    root.title("show-{}".format(query))
    label = tkinter.Label(root)

    button_prev = tkinter.Button(root, text="Back",
                                 command=on_back,
                                 state=tkinter.DISABLED)
    button_prev.pack(fill=tkinter.X)
    button_next = tkinter.Button(root, text="Next",
                                 command=on_next,
                                 state=tkinter.ACTIVE)
    button_next.pack(fill=tkinter.X)
    label.pack(fill=tkinter.X)


def main():
    global pics, pic_ind
    init_gui()
    pics = list(get_images_from_directory(directory))
    if len(pics) == 0:
        download_pic()
    change_pic(directory + "/" + pics[0])
    if len(pics) == 1:
        download_pic()
        
    root.mainloop()


if __name__ == "__main__":
    main()
