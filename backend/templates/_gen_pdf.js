const fs = require('fs');
const html = <!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  @page { size: A4; margin: 2cm 2.5cm; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: sans-serif; font-size: 11pt; color: #333; line-height: 1.6; }
  .page { page-break-after: always; }
  .page:last-child { page-break-after: avoid; }
  .header { text-align: center; margin-bottom: 24px; border-bottom: 2px solid #2c5aa0; padding-bottom: 16px; }
  .header h1 { font-size: 24pt; color: #2c5aa0; margin-bottom: 4px; }
  .header .title { font-size: 14pt; color: #555; margin-bottom: 8px; }
  .contact-row { display: flex; justify-content: center; gap: 24px; font-size: 10pt; color: #666; }
  .summary { margin-top: 12px; font-size: 10.5pt; color: #444; text-align: left; padding: 0 20px; }
  .section { margin-bottom: 20px; }
  .section h2 { font-size: 14pt; color: #2c5aa0; border-bottom: 1px solid #ddd; padding-bottom: 6px; margin-bottom: 12px; }
  .item { margin-bottom: 14px; }
  .item-header { display: flex; justify-content: space-between; align-items: baseline; }
  .item-title { font-size: 12pt; font-weight: bold; color: #222; }
  .item-subtitle { font-size: 10.5pt; color: #555; }
  .item-date { font-size: 10pt; color: #888; }
  .item-desc { font-size: 10.5pt; color: #444; margin-top: 4px; white-space: pre-wrap; }
  .item-meta { font-size: 10pt; color: #666; margin-top: 2px; }
  .skill-grid { display: flex; flex-wrap: wrap; gap: 8px; }
  .skill-tag { display: inline-block; background: #e8f0fe; color: #2c5aa0; padding: 4px 12px; border-radius: 4px; font-size: 10pt; }
  .skill-bar { display: inline-block; width: 60px; height: 6px; background: #ddd; border-radius: 3px; margin-left: 6px; vertical-align: middle; }
  .skill-fill { display: block; height: 100%; background: #2c5aa0; border-radius: 3px; }
  .text-content { font-size: 10.5pt; color: #444; white-space: pre-wrap; line-height: 1.8; }
  .footer { text-align: center; font-size: 9pt; color: #aaa; margin-top: 40px; }
</style>
</head>
<body>
{% for module in modules %}
<div class="page">
  {% if module.key == "personal_info" %}
    <div class="header">
      <h1>{{ module.username }}</h1>
      <div class="title">{{ module.title }}</div>
      <div class="contact-row">
        <span>u{90ae}u{7bb1}: {{ module.email }}</span>
        <span>u{7535}u{8bdd}: {{ module.phone }}</span>
      </div>
      {% if module.summary %}
      <div class="summary">{{ module.summary }}</div>
      {% endif %}
    </div>
  {% else %}
    <div class="section">
      <h2>{{ module.name }}</h2>
      {% if module.type == "list" %}
        {% for item in module.items %}
        <div class="item">
          <div class="item-header">
            {% if item.school %}
              <span class="item-title">{{ item.school }}</span>
              <span class="item-date">{{ item.start_date|default:"" }} ~ {{ item.end_date|default:"u{81f3}u{4eca}" }}</span>
            {% elif item.company %}
              <span class="item-title">{{ item.company }} - {{ item.position|default:"" }}</span>
              <span class="item-date">{{ item.start_date|default:"" }} ~ {{ item.end_date|default:"u{81f3}u{4eca}" }}</span>
            {% elif item.name %}
              <span class="item-title">{{ item.name }}{% if item.role %} ({{ item.role }}){% endif %}</span>
              <span class="item-date">{{ item.start_date|default:"" }} ~ {{ item.end_date|default:"u{81f3}u{4eca}" }}</span>
            {% endif %}
          </div>
          {% if item.degree %}<div class="item-subtitle">{{ item.degree }} | {{ item.major|default:"" }}</div>{% endif %}
          {% if item.tech_stack %}<div class="item-meta">u{6280}u{672f}u{6808}: {{ item.tech_stack }}</div>{% endif %}
          {% if item.description %}<div class="item-desc">{{ item.description }}</div>{% endif %}
        </div>
        {% endfor %}
      {% elif module.type == "skills" %}
        <div class="skill-grid">
          {% for item in module.items %}
          <span class="skill-tag">
            {{ item.name }} ({{ item.level }}%)
            <span class="skill-bar"><span class="skill-fill" style="width: {{ item.level }}%"></span></span>
          </span>
          {% endfor %}
        </div>
      {% elif module.type == "text" %}
        <div class="text-content">{{ module.content|default:"u{6682}u{65e0}u{5185}u{5bb9}" }}</div>
      {% endif %}
    </div>
  {% endif %}
  {% if forloop.last %}
  <div class="footer">u{7531}u{667a}u{80fd}u{7b80}u{5386}u{7ba1}u{7406}u{7cfb}u{7edf}u{751f}u{6210}</div>
  {% endif %}
</div>
{% endfor %}
</body>
</html>;
fs.writeFileSync(process.argv[1], html, 'utf8');
console.log('template written');
