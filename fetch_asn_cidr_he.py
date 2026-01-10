import requests
from bs4 import BeautifulSoup
import argparse
import os
import time
import random
import sys
import json
import re

def load_asn_data(filepath='asn_data.json'):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_asn_data(data, filepath='asn_data.json'):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def fetch_cidr(asn):
    # 处理 ASN 格式
    asn = asn.upper()
    if not asn.startswith('AS'):
        asn = f'AS{asn}'

    url = f"https://bgp.he.net/{asn}#_prefixes"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Referer": "https://bgp.he.net/"
    }

    print(f"正在获取 {asn} 的数据... ({url})")
    
    try:
        # 添加随机延迟以模拟人类行为
        time.sleep(random.uniform(2, 5))
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 403:
            print(f"错误: 访问被拒绝 (403)。bgp.he.net 可能检测到了爬虫。")
            return False
            
        if response.status_code != 200:
            print(f"错误: HTTP 状态码 {response.status_code}")
            return False

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取 ASN 名称
        asn_name = "Unknown"
        page_title = soup.title.string if soup.title else ""
        # 尝试匹配 "ASxxxxx (Name) ..." 格式
        match = re.search(r'AS\d+\s+\((.*?)\)', page_title)
        if match:
            asn_name = match.group(1)
        else:
            # 备用：尝试从 h1 或其他位置获取，或者直接使用 title 的一部分
            if page_title:
                parts = page_title.split(' ', 1)
                if len(parts) > 1:
                    asn_name = parts[1].split('-')[0].strip()
        
        print(f"ASN 名称: {asn_name}")

        # 查找前缀表格
        ipv4_prefixes = []
        ipv6_prefixes = []
        
        # 提取 IPv4
        table4 = soup.find('table', id='table_prefixes4')
        if table4:
            tbody = table4.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if cols and len(cols) > 0:
                        prefix = cols[0].get_text(strip=True)
                        if '/' in prefix:
                            ipv4_prefixes.append(prefix)
                            
        # 提取 IPv6
        table6 = soup.find('table', id='table_prefixes6')
        if table6:
            tbody = table6.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if cols and len(cols) > 0:
                        prefix = cols[0].get_text(strip=True)
                        if '/' in prefix:
                            ipv6_prefixes.append(prefix)

        print(f"找到 {len(ipv4_prefixes)} 个 IPv4 前缀, {len(ipv6_prefixes)} 个 IPv6 前缀。")

        # 保存结果到文件
        output_dir = 'ASN_CIDR'
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存 IPv4
        if ipv4_prefixes:
            filename = os.path.join(output_dir, f"{asn}.conf")
            with open(filename, 'w') as f:
                f.write(f"# {asn} {asn_name} IPv4 CIDR list from bgp.he.net\n")
                f.write(f"# Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} UTC\n")
                for net in ipv4_prefixes:
                    f.write(f"route {net} via \"lo\";\n")
            print(f"已保存: {filename}")
        
        # 保存 IPv6
        if ipv6_prefixes:
            filename_v6 = os.path.join(output_dir, f"{asn}_IPv6.conf")
            with open(filename_v6, 'w') as f:
                f.write(f"# {asn} {asn_name} IPv6 CIDR list from bgp.he.net\n")
                f.write(f"# Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} UTC\n")
                for net in ipv6_prefixes:
                    f.write(f"route {net} via \"lo\";\n")
            print(f"已保存: {filename_v6}")
            
        # 更新 JSON 数据
        current_data = load_asn_data()
        current_data[asn] = {
            "asn": asn,
            "name": asn_name,
            "v4_count": len(ipv4_prefixes),
            "v6_count": len(ipv6_prefixes),
            "updated_at": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        }
        save_asn_data(current_data)
            
        return True

    except Exception as e:
        print(f"发生异常: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='从 bgp.he.net 获取 ASN CIDR')
    parser.add_argument('asn', help='AS号 (例如 AS13335)')
    args = parser.parse_args()
    
    success = fetch_cidr(args.asn)
    if not success:
        sys.exit(1)
