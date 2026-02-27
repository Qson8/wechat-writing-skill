"""
scripts/
├── render_images.py          ← 渲染封面图、对比表、流程图、功能卡片
└── post_image_templates.pen  ← 封面图排版模板（JSON格式）

用法示例：

  from scripts.render_images import render_cover, render_comparison, render_workflow

  render_cover(
      title="刚开源2700 Star，这个Agent框架能让AI替你自动干活",
      subtitle="一个人管多条流程，产出相当于一个团队",
      output_path="cover.png",
      template_path="scripts/post_image_templates.pen"
  )

依赖安装：
  pip install pillow
"""
