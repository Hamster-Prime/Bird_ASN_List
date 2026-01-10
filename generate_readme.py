import json
import os
import time

def generate_readme(data_file='asn_data.json', output_file='README.md'):
    if not os.path.exists(data_file):
        print(f"警告: 数据文件 {data_file} 不存在。")
        return

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取数据文件失败: {e}")
        return

    update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    
    # 统计信息
    total_asns = len(data)
    total_v4 = sum(item['v4_count'] for item in data.values())
    total_v6 = sum(item['v6_count'] for item in data.values())

    # 生成 Markdown 内容
    content = f"""# 全球 ASN CIDR 列表

**说明：** 此数据每日从 [bgp.he.net](https://bgp.he.net/) 自动获取。

---

## 📊 统计信息

**最后更新时间：** {update_time} UTC

### 📦 概览
- **包含数据的 ASN 总数：** {total_asns}
- **IPv4 CIDR 总数：** {total_v4}
- **IPv6 CIDR 总数：** {total_v6}

### 🛠️ ASN CIDR 详情列表

| ASN | 名称 | IPv4 数量 | IPv6 数量 | 更新时间 (UTC) |
|-----|------|-----------|-----------|----------------|
"""

    # 排序：按 IPv4 数量降序，或者按 ASN 号排序
    # 这里按 ASN 字典序排序
    sorted_asns = sorted(data.keys(), key=lambda x: int(x.replace('AS', '')) if x.replace('AS', '').isdigit() else x)

    for asn in sorted_asns:
        info = data[asn]
        name = info.get('name', 'Unknown')
        v4 = info.get('v4_count', 0)
        v6 = info.get('v6_count', 0)
        updated = info.get('updated_at', '-')
        
        content += f"| {asn} | {name} | {v4} | {v6} | {updated} |\n"

    content += """
---
*此信息由 GitHub Actions 自动更新*
"""

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"成功生成 {output_file}")
    except Exception as e:
        print(f"写入 README 失败: {e}")

if __name__ == "__main__":
    generate_readme()
