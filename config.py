from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""
    images_path: str = r"D:\MyPython\nonebot\NyarukoBot\nyarukobot\plugins\nsyimages\images"
    alias_file: str = r"D:\MyPython\nonebot\NyarukoBot\nyarukobot\plugins\nsyimages\alias.json"