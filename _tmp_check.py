import os

files = [
    r'F:\SmartResume\smart-resume-hub\frontend\src\router\index.js',
    r'F:\SmartResume\smart-resume-hub\frontend\src\views\user\ResumeDetail.vue',
    r'F:\SmartResume\smart-resume-hub\frontend\src\views\user\ResumeEdit.vue',
    r'F:\SmartResume\smart-resume-hub\frontend\src\components\Layout.vue',
    r'F:\SmartResume\smart-resume-hub\frontend\src\api\index.js',
]

for fp in files:
    with open(fp, 'r', encoding='utf-8') as f:
        c = f.read()
    name = os.path.basename(fp)
    issues = []
    if chr(65279) in c:
        issues.append('BOM')
    # Check brace balance for JS files
    if fp.endswith('.js'):
        opens_curly = c.count('{')
        closes_curly = c.count('}')
        if opens_curly != closes_curly:
            issues.append(f'Unbalanced braces: {{={opens_curly}, }}={closes_curly}')
        opens_bracket = c.count('[')
        closes_bracket = c.count(']')
        if opens_bracket != closes_bracket:
            issues.append(f'Unbalanced brackets: [={opens_bracket}, ]={closes_bracket}')
    if issues:
        print(f'ISSUES in {name}: {chr(44).join(issues)}')
    else:
        print(f'OK: {name}')

print()
# Verify the router specifically
print('=== Router structure check ===')
fp = r'F:\SmartResume\smart-resume-hub\frontend\src\router\index.js'
with open(fp, 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(98, min(108, len(lines))):
    print(f'{i+1}: {lines[i].rstrip()}')
