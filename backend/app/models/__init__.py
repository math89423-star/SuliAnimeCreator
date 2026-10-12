"""LEGACY 占位：业务真源是 data/*.json（见 services/disk_store + services/repo）。
本文件仅保留 SQLAlchemy 建表兼容，不写业务读/写。新代码不要再引用 db。
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Project(db.Model):
    id = db.Column(db.String, primary_key=True)  # PRJ-xxxxxx
    name = db.Column(db.String, default="")
    style_bible = db.Column(db.Text, default="")

class Story(db.Model):
    id = db.Column(db.String, primary_key=True)  # STY-xxxxxx
    project_id = db.Column(db.String, index=True)
    title = db.Column(db.String, default="")
    logline = db.Column(db.Text, default="")
    topview_md = db.Column(db.Text, default="")  # 来自 MirrorStage story_topview
    status = db.Column(db.String, default="draft")  # draft/suggested/confirmed

class Character(db.Model):
    id = db.Column(db.String, primary_key=True)  # CHAR-xxxx
    project_id = db.Column(db.String, index=True)
    name = db.Column(db.String, default="")
    # 四维：发型/面部/体态/身份 + 展示名中英（沿用两边规范）
    data = db.Column(db.JSON, default=dict)

class ScriptEpisode(db.Model):
    id = db.Column(db.String, primary_key=True)  # EP-xxxxxx
    project_id = db.Column(db.String, index=True)
    code = db.Column(db.String, default="EP001")
    title = db.Column(db.String, default="")
    screenplay_md = db.Column(db.Text, default="")
    segs_json = db.Column(db.JSON, default=list)
    verdict = db.Column(db.String, default="draft")  # draft/PASS/REVISE/BLOCK/APPROVE

class BoardShot(db.Model):
    id = db.Column(db.String, primary_key=True)  # SHOT-xxx
    episode_id = db.Column(db.String, index=True)
    source_sc_ids = db.Column(db.JSON, default=list)
    duty = db.Column(db.String, default="")
    duration_s = db.Column(db.Float, default=0)
    camera = db.Column(db.JSON, default=dict)
    start_boundary = db.Column(db.JSON, default=dict)
    end_boundary = db.Column(db.JSON, default=dict)
    keyframe_en = db.Column(db.Text, default="")
    sort_order = db.Column(db.Integer, default=0)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    episode_id = db.Column(db.String, index=True)
    verdict = db.Column(db.String, default="draft")
    findings = db.Column(db.JSON, default=list)

class PromptSnapshot(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shot_id = db.Column(db.String, index=True)
    assembled_en = db.Column(db.Text, default="")
    locks_hit = db.Column(db.JSON, default=list)
