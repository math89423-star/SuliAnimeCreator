---
name: restful-modular
description: 后端模块化与 RESTful 接口总纲。Flask Blueprint 拆分 + 资源建模四步（对象→URI→表示→方法）在本仓的落地：六蓝图、名词 URI、集合/单体、统一信封、落盘。触发词：后端、蓝图、接口、REST、API、落盘、blueprint。
sources:
  - https://flask.palletsprojects.com/en/stable/blueprints/
  - https://restfulapi.net/rest-api-design-tutorial-with-example/
---

# RESTful Modular（后端模块化与接口）

> 联网依据：模块化取 [Flask Blueprints](https://flask.palletsprojects.com/en/stable/blueprints/)；资源设计四步取 [How to Design a REST API](https://restfulapi.net/rest-api-design-tutorial-with-example/)（Identify object model → Create model URIs → Representations → HTTP methods）。本仓六蓝图与 JSON 落盘为附加实现。

## 1. 模块化（Flask 原文映射）

- 用 Blueprint 把应用拆成集合：建 app 对象、初始化扩展、注册一组 blueprint；大应用标准做法。([来源](https://flask.palletsprojects.com/en/stable/blueprints/))
- 挂载：`app.register_blueprint(bp)`，可带 `url_prefix`（本仓 `/api/v1/story` 等）； endpoint 按 `蓝图名.函数名`（`url_for('admin.index')`，同蓝图内可用 `.index` 相对引用）。([来源](https://flask.palletsprojects.com/en/stable/blueprints/))
- Blueprint 只记录“注册时要执行的操作”，不是完整 app；一旦注册不可注销（要拆只能重建 app）。([来源](https://flask.palletsprojects.com/en/stable/blueprints/))
- Blueprint 级 `errorhandler` 与 app 同写法；404/405 特殊：无效 URL 时蓝图处理器不触发（蓝图不拥有 URL 空间），API 统一错误建议在 app 层按 `request.path.startswith('/api/')` 分流。([来源](https://flask.palletsprojects.com/en/stable/blueprints/))→ 本仓：成功 `{code:0,data}`、失败 `{code:4xxx,msg}` 全局统一，前端直接判 code。

## 2. 资源设计四步（restfulapi.net 原文映射）

- 先定对象模型（devices/configurations 二资源示例：顶层+子资源，各有唯一 id）。([来源](https://restfulapi.net/rest-api-design-tutorial-with-example/))→ 本仓：story/character/outfit/shot/review/prompt 六资源，各有 `CHAR-/SHOT-` 等稳定 id。
- URI 全名词禁动词；集合与单体两形态（`/devices` vs `/devices/{id}`），子集合（`/devices/{id}/configurations`）复用主集合字段不另起表示。([来源](https://restfulapi.net/rest-api-design-tutorial-with-example/))
- 表示：集合只给关键字段保小包，单体给全量+子资源链接（HATEOAS 自描述）。([来源](https://restfulapi.net/rest-api-design-tutorial-with-example/))→ 本仓：列表（角色/分镜/版本）只给关键列，详情（pack/assemble）给全量+关联。
- 方法：浏览 `GET /devices`（大集合 `?startIndex&size` 分页过滤）、子集合 `GET /devices/{id}/configurations`。([来源](https://restfulapi.net/rest-api-design-tutorial-with-example/))→ 本仓：`GET` 查、`POST` 建/动作、 `PUT` 全量改、`DELETE` 删；分页参数统一 `?page&page_size`（前端 `usePagination` 对齐）。

## 3. 本仓落地

- 六蓝图：`story/character/scriptboard/director/uploads/art`，注册表唯一出处 `backend/app/__init__.py`，健康口 `GET /api/health` 列蓝图名。
- 落盘：`backend/app/services/disk_store.py` 管 `backend/data/*.json`，启动 `load`、写后立刻 `save`；可写区仅此一处。
- 门禁：新接口必配 `test_client` 正常+异常双分支；文档（`skills/README`/`docs/FILE_LAYOUT`）同步更新。
