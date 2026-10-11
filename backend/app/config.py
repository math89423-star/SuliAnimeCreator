import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///suli.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 边界：整合项目依然不直连任何图像/视频生成，只出提示词文本
    FORBIDDEN_KEYS = ["SD_API_KEY", "KLING_API_KEY", "JIMENG_API_KEY", "OPENAI_IMAGE_KEY"]
