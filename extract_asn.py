import pandas as pd
import os
import argparse
import sys

# 设置命令行参数解析
parser = argparse.ArgumentParser(description='根据AS号从ipinfo_lite.csv导出CIDR')
parser.add_argument('asn', help='要导出的AS号 (例如: AS13335 或 13335)')
args = parser.parse_args()

# 处理输入的ASN，确保格式为 ASxxxxx
target_asn = args.asn.upper()
if not target_asn.startswith('AS'):
    target_asn = f'AS{target_asn}'

input_file = 'ipinfo_lite.csv'

if not os.path.exists(input_file):
    print(f"错误: 未找到文件 {input_file}")
    sys.exit(1)

print(f"正在读取 {input_file}...")
# 读取CSV文件
# 指定dtype以防pandas推断错误，虽然asn列通常是字符串
df = pd.read_csv(input_file, dtype={'asn': str})

# 过滤出指定ASN的行
df_asn = df[df['asn'] == target_asn].copy()

if df_asn.empty:
    print(f"未找到 ASN 为 {target_asn} 的记录。")
    sys.exit(0)

# 过滤 IPv4 和 IPv6
df_ipv4 = df_asn[~df_asn['network'].str.contains(':')].copy()
df_ipv6 = df_asn[df_asn['network'].str.contains(':')].copy()

output_dir = 'ASN_CIDR'
os.makedirs(output_dir, exist_ok=True)

# 导出 IPv4
if not df_ipv4.empty:
    filename = os.path.join(output_dir, f"{target_asn}.conf")
    print(f"正在生成 {filename} ({len(df_ipv4)} 条记录)...")
    
    with open(filename, 'w') as f:
        f.write(f"# {target_asn} cidr address-list\n")
        for net in df_ipv4['network']:
            if '/' not in str(net):
                net = f"{net}/32"
            f.write(f"route {net} via \"lo\";\n")
else:
    print(f"没有找到 {target_asn} 的 IPv4 记录。")

# 导出 IPv6
if not df_ipv6.empty:
    filename_v6 = os.path.join(output_dir, f"{target_asn}_IPv6.conf")
    print(f"正在生成 {filename_v6} ({len(df_ipv6)} 条记录)...")
    
    with open(filename_v6, 'w') as f:
        f.write(f"# {target_asn} IPv6 cidr address-list\n")
        for net in df_ipv6['network']:
            if '/' not in str(net):
                net = f"{net}/128"
            f.write(f"route {net} via \"lo\";\n")
else:
    print(f"没有找到 {target_asn} 的 IPv6 记录。")

print("处理完成！")
