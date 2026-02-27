# 完整自动化流水线

## 流程概览

```
run(topic)
    ↓
① AI 生成文章（标题 / 钩子 / 摘要 / 正文 / 互动钩子）
    ↓
② 渲染封面图（基于 .pen 模板）
   渲染对比表（可选）
   渲染流程图（可选）
    ↓
③ 批量上传图片到微信素材库
    ↓
④ 推送草稿箱
    ↓
⑤ 手动登录后台发布
```

## 环境准备

```bash
# 安装依赖
pip install openai requests pillow schedule

# 配置环境变量
export WECHAT_APP_ID="你的AppID"
export WECHAT_APP_SECRET="你的AppSecret"
export OPENAI_API_KEY="你的OpenAI Key"

# 可选：指定 skill 和模板路径
export SKILL_WRITE_PATH="./SKILL.md"
export PEN_TEMPLATE_PATH="./scripts/post_image_templates.pen"
```

## 获取微信 AppID 和 AppSecret

1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 设置与开发 → 基本配置
3. 复制 AppID 和 AppSecret
4. IP 白名单：把你服务器的 IP 加进去（本地测试加你的本机 IP）

## 运行

```bash
# 单次运行（手动指定主题）
python main.py

# 定时运行（每天早上9点自动生成）
# 取消 main.py 底部的注释：
# schedule.every().day.at("09:00").do(scheduled_job)
```

## 注意事项

- 订阅号草稿箱 API 每天调用次数约 10000 次，正常使用够用
- 图片素材永久库上限：订阅号 1000 个，注意定期清理
- 推荐先备份再用，项目刚上线时建议人工校对后再发布
- access_token 有效期 2 小时，脚本每次运行自动刷新

## 常见错误

| 错误码 | 原因 | 解决方法 |
|--------|------|----------|
| 40001 | AppSecret 错误或 IP 未白名单 | 检查配置，加 IP 白名单 |
| 45009 | 当天接口调用超限 | 明天再试 |
| 40007 | media_id 无效 | 图片上传失败，检查图片格式和大小 |
