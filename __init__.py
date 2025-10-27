from nonebot import get_plugin_config
from nonebot.plugin import on_command
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg, ArgPlainText
from nonebot.log import logger
from .config import Config
import os
import random
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment, MessageEvent
import httpx
import ssl
from DownloadKit import DownloadKit

__plugin_meta__ = PluginMetadata(
    name="nsyimages",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

images_path = r"D:\MyPython\nonebot\NyarukoBot\nyarukobot\plugins\nsyimages\images"

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
ssl_context.set_ciphers("DEFAULT@SECLEVEL=2")

def update_names():
    global names
    names = [d for d in os.listdir(images_path) if os.path.isdir(os.path.join(images_path, d))]

def rplyimg(name):
    imgdir = images_path + "\\" + name
    files = os.listdir(imgdir)
    random_img = random.choice(files)
    url =r"file:///" + imgdir + "\\" +random_img
    img = MessageSegment(type = "image", data = {"file": url})
    text = MessageSegment.text(f"{random_img}，若与人物不符或您不喜欢这张图片，请联系bot主删除ww")
    return (img, text)

nsy_list = on_command("nsy列表", aliases={"女声优列表"}, priority = 3, block = True)
@nsy_list.handle()
async def namelist(bot: Bot):
    update_names()
    rpl = f"支持查询的声优有：{names[0]}"
    for name in names:
        if name != names[0]:
            rpl += "，" + name
    await nsy_list.finish(rpl)

nsy = on_command("nsy", aliases={"女声优"}, priority = 4, block = True)
@nsy.handle()
async def _(bot:Bot, args: Message = CommandArg()):
    update_names()
    if name := args.extract_plain_text():
        if name not in names:
            await nsy.finish('不包含您所查询的声优哦，您可以自行添加ww')
        else:
            (img, text) = rplyimg(name)
            await nsy.send(img)
            await nsy.finish(text)

nsy_add = on_command("添加nsy", aliases={"添加女声优"}, priority = 4, block = True)
@nsy_add.handle()
async def __(bot:Bot, args: Message = CommandArg()):
    update_names()
    if name := args.extract_plain_text():
        if name in names:
            await nsy_add.finish('该声优已经存在了喵')
        else:
            global addname
            addname = name
            await nsy_add.skip()
@nsy_add.got("confirm",prompt="如果你确认这是该声优的全名并且没有错别字，请发送yes，否则请重新发送名字，可发送0以撤回请求")
async def ___(bot:Bot, confirm:str = ArgPlainText()):
    if confirm == '0':
        await nsy_add.finish("已结束交互")
    imgdir = images_path + "\\" + (addname if confirm == 'yes' else confirm)
    os.mkdir(imgdir)
    await nsy_add.finish("添加成功")

nsy_upload = on_command("上传nsy", aliases={"上传女声优"}, priority = 4, block = True)
@nsy_upload.got("name", prompt="请发送声优全名（非昵称）")
async def ____(bot:Bot, name:str = ArgPlainText()):
    update_names()
    if name not in names:
        await nsy_upload.finish('不包含该声优哦，您可以自行添加ww')
    else:
        global upname
        global cnt
        upname = name
        cnt = 0
        await nsy_upload.send("请发送图片（支持多张），并发送“完成”")
        await nsy_upload.skip()
@nsy_upload.got("msg")
async def receive_img(bot: Bot, event: MessageEvent):
    msg = event.message
    print(len(msg))
    d = DownloadKit()
    global cnt
    for seg in msg:
        print(seg)
        if seg.type == "image":
            url = seg.data["url"]
            print(url)
            try:
                cnt += 1
                d.add(url, save_path= images_path + "\\" + upname, rename= f"{len(os.listdir(images_path + "\\" + upname))+501}.jpg")
            except Exception as e:
                logger.warning(f"下载图片失败: {e}")
                continue
        elif seg.type == "text":
            if seg.data["text"] == "完成":
                await nsy_upload.send(f"已成功上传{cnt}张图片")
                cnt = 0
                await nsy_upload.finish()
    await nsy_upload.reject()

nsy_help = on_command("nsyhelp", aliases={"nsy帮助"}, priority = 3, block = True)
@nsy_help.handle()
async def _____(bot: Bot):
    help = """nsy+名字 → 获取一张女声优图片
看nsy → 获取一张随机nsy图片
nsy列表 → 查看当前可查询的女声优列表
添加nsy+名字 → 新添一个女声优以供查询
上传nsy → 根据提示自行上传女声优的照片丰富图片库
（加号无需打出来，可以用空格或什么都不加）"""
    await nsy_help.finish(help)

nsy_random = on_command("看nsy", priority = 3, block = True)
@nsy_random.handle()
async def ______(bot: Bot):
    update_names()
    await nsy_random.finish(rplyimg(random.choice(names))[0])