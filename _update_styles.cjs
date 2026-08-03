const fs = require('fs');
const path = require('path');

function updateFile(filePath, replacements) {
  const fullPath = path.resolve(__dirname, filePath);
  let content = fs.readFileSync(fullPath, 'utf8');
  for (const [pattern, replacement] of replacements) {
    content = content.replace(pattern, replacement);
  }
  fs.writeFileSync(fullPath, content, 'utf8');
  console.log('Updated: ' + filePath);
}

// Vue3 Login.vue
updateFile('frontend/src/views/Login.vue', [
  [/radial-gradient\(circle at top left, rgba\(64, 158, 255, 0\.14\), transparent 34%\),\s*linear-gradient\(180deg, #f5f7fa 0%, #eef2f7 100%\);/g, '#f5f5f7;'],
  [/background: linear-gradient\(135deg, #0f172a 0%, #1d4ed8 100%\);/g, 'background: #272729;'],
  [/border-radius: 14px;/g, 'border-radius: 9999px;'],
  [/background: rgba\(255, 255, 255, 0\.16\);/g, 'background: rgba(210, 210, 215, 0.16);'],
  [/font-size: 28px;\s*line-height: 1\.2;/g, 'font-size: 40px;\n  font-weight: 600;\n  line-height: 1.1;\n  letter-spacing: -0.2px;'],
  [/color: rgba\(255, 255, 255, 0\.82\);\s*font-size: 14px;/g, 'color: #cccccc;\n  font-size: 17px;\n  line-height: 1.47;'],
  [/color: rgba\(255, 255, 255, 0\.92\);/g, 'color: #cccccc;'],
  [/border: 1px solid #ebeef5;\s*border-radius: 16px;\s*box-shadow: 0 12px 36px rgba\(15, 23, 42, 0\.08\);/g, 'border: 1px solid #e0e0e0;\n  border-radius: 18px;\n  box-shadow: none;'],
  [/font-size: 20px;\s*color: #333333;/g, 'font-size: 28px;\n  font-weight: 600;\n  letter-spacing: -0.15px;\n  color: #1d1d1f;'],
  [/color: #666666;/g, 'color: #7a7a7a;'],
  [/font-size: 15px;\s*border-radius: 8px;/g, 'font-size: 17px;\n  border-radius: 9999px;'],
  [/border-radius: 14px 14px 0 0;/g, 'border-radius: 18px 18px 0 0;'],
  [/border-radius: 0 0 14px 14px;/g, 'border-radius: 0 0 18px 18px;'],
]);

console.log('Login.vue done');
