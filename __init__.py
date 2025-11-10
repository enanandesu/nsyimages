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
import json

__plugin_meta__ = PluginMetadata(
    name="nsyimages",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

images_path = config.images_path

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
ssl_context.set_ciphers("DEFAULT@SECLEVEL=2")

def update_alias_list():
    global alias_list
    try:
        with open(config.alias_file, 'r', encoding='utf-8') as f:
            alias_list = json.load(f)
    except FileNotFoundError:
        alias_list = {}
        with open(config.alias_file, 'w', encoding='utf-8') as f:
            json.dump(alias_list, f, ensure_ascii=False, indent=4)

def update_whitelist():
    global whitelist
    try:
        with open(config.whitelist_file, 'r', encoding='utf-8') as f:
            whitelist = json.load(f)
    except FileNotFoundError:
        whitelist = {}
        with open(config.whitelist_file, 'w', encoding='utf-8') as f:
            json.dump(whitelist, f, ensure_ascii=False, indent=4)

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
async def namelist(bot: Bot, event: MessageEvent):
    update_names()
    update_whitelist()
    group_id = str(event.get_session_id()).split("_")[1]
    for name in names:
        if name in whitelist:
            if group_id in whitelist[name]:
                pass
            else:
                names.remove(name)
    rpl = f"支持查询的声优有：{names[0]}"
    for name in names:
        if name != names[0]:
            rpl += "，" + name
    await nsy_list.finish(rpl)

nsy = on_command("nsy", aliases={"女声优"}, priority = 4, block = True)
@nsy.handle()
async def _(bot:Bot, event: MessageEvent, args: Message = CommandArg()):
    update_names()
    update_alias_list()
    update_whitelist()
    group_id = str(event.get_session_id()).split("_")[1]
    for name in names:
        if name in whitelist:
            if group_id in whitelist[name]:
                pass
            else:
                names.remove(name)
    if aname := args.extract_plain_text():
        tmp = aname.split()
        if len(tmp) != 1:
            await nsy.finish("请发送单个声优全名或别名")
        real_name = alias_list.get(aname, aname)
        if real_name not in names:
            await nsy.finish('不包含您所查询的声优哦，您可以自行添加ww')
        else:
            (img, text) = rplyimg(real_name)
            await nsy.send(img)
            await nsy.finish(text)

nsy_add = on_command("添加nsy", aliases={"添加女声优"}, priority = 4, block = True)
@nsy_add.handle()
async def __(bot:Bot, args: Message = CommandArg()):
    update_names()
    if name := args.extract_plain_text():
        tmp = name.split()
        if len(tmp) != 1:
            await nsy_add.finish("请发送单个声优全名（非昵称）")
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
@nsy_upload.got("name", prompt="请发送声优全名或别名")
async def ____(bot:Bot, event:MessageEvent, name:str = ArgPlainText()):
    update_names()
    update_alias_list()
    update_whitelist()
    group_id = str(event.get_session_id()).split("_")[1]
    for n in names:
        if n in whitelist:
            if group_id in whitelist[n]:
                pass
            else:
                names.remove(n)
    real_name = alias_list.get(name, name)
    if real_name not in names:
        await nsy_upload.finish('不包含该声优哦，您可以自行添加ww')
    else:
        global upname
        global cnt
        upname = real_name
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
    help = """nsy + 全名/别名 → 获取一张女声优图片
看nsy → 获取一张随机nsy图片
nsy列表 → 查看当前可查询的女声优列表
nsy别名 + 全名 → 查询该声优的所有别名
添加nsy别名 + 全名 + 别名 → 为已有声优添加别名
nsy图片数 + 全名/别名 → 查询该声优的图片数量
添加nsy + 全名 → 新添一个女声优以供查询
上传nsy → 根据提示自行上传女声优的照片丰富图片库"""
    await nsy_help.finish(help)

nsy_random = on_command("看nsy", priority = 3, block = True)
@nsy_random.handle()
async def ______(bot: Bot, event: MessageEvent):
    update_names()
    update_whitelist()
    group_id = str(event.get_session_id()).split("_")[1]
    for name in names:
        if name in whitelist:
            if group_id in whitelist[name]:
                pass
            else:
                names.remove(name)
    await nsy_random.finish(rplyimg(random.choice(names))[0])

add_nsy_alias = on_command("添加nsy别名", aliases={"添加女声优别名"}, priority = 4, block = True)
@add_nsy_alias.handle()
async def _______(bot:Bot, event:MessageEvent, args: Message = CommandArg()):
    update_names()
    update_alias_list()
    update_whitelist()
    group_id = str(event.get_session_id()).split("_")[1]
    for name in names:
        if name in whitelist:
            if group_id in whitelist[name]:
                pass
            else:
                names.remove(name)
    if fulltext := args.extract_plain_text():
        tmp = fulltext.split()
        if len(tmp) != 2:
            await add_nsy_alias.finish("请按照格式：“添加nsy别名 声优全名 别名” 进行添加")
        real_name, alias = tmp
        if real_name not in names:
            await add_nsy_alias.finish('不包含您所查询的声优哦，您可以自行添加ww')
        else:
            if alias in alias_list:
                await add_nsy_alias.finish(f"别名{alias}已存在，请更换别名后重试")
            alias_list[alias] = real_name
            with open(config.alias_file, 'w', encoding='utf-8') as f:
                json.dump(alias_list, f, ensure_ascii=False, indent=4)
            await add_nsy_alias.finish(f"成功为{real_name}添加别名{alias}")

nsy_alias = on_command("nsy别名", aliases={"女声优别名"}, priority = 3, block = True)
@nsy_alias.handle()
async def ________(bot:Bot, event:MessageEvent, args: Message = CommandArg()):
    update_names()
    update_alias_list()
    update_whitelist()
    group_id = str(event.get_session_id()).split("_")[1]
    for name in names:
        if name in whitelist:
            if group_id in whitelist[name]:
                pass
            else:
                names.remove(name)
    if fulltext := args.extract_plain_text():
        tmp = fulltext.split()
        if len(tmp) != 1:
            await nsy_alias.finish("请发送单个声优全名（非昵称）")
        real_name = tmp[0]
        if real_name not in names:
            await nsy_alias.finish('不包含您所查询的声优哦，您可以自行添加ww')
        else:
            aliases = [alias for alias, name in alias_list.items() if name == real_name]
            if not aliases:
                await nsy_alias.finish(f"{real_name}目前没有别名哦")
            else:
                rpl = f"{real_name}的别名有：{aliases[0]}"
                for alias in aliases:
                    if alias != aliases[0]:
                        rpl += "，" + alias
                await nsy_alias.finish(rpl)

counter = on_command("nsy图片数", aliases={"女声优图片数"}, priority = 3, block = True)
@counter.handle()
async def _________(bot:Bot, event:MessageEvent, args: Message = CommandArg()):
    update_names()
    update_alias_list()
    update_whitelist()
    group_id = str(event.get_session_id()).split("_")[1]
    for name in names:
        if name in whitelist:
            if group_id in whitelist[name]:
                pass
            else:
                names.remove(name)
    if aname := args.extract_plain_text():
        tmp = aname.split()
        if len(tmp) != 1:
            await counter.finish("请发送单个声优全名或别名")
        real_name = alias_list.get(aname, aname)
        if real_name not in names:
            await counter.finish('不包含您所查询的声优哦，您可以自行添加ww')
        else:
            imgdir = images_path + "\\" + real_name
            files = os.listdir(imgdir)
            await counter.finish(f"{real_name}共有{len(files)}张图片")