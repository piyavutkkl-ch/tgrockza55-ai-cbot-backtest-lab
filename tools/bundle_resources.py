import os, shutil, zipfile

src_prompt = r'd:\cbot-atgvt\MISSION_PROMPT.md'
src_arch = r'd:\cbot-atgvt\ARCHITECTURE.md'
src_btest = r'd:\cbot-atgvt\docs\data\backtest_data.json'
src_live = r'd:\cbot-atgvt\docs\data\live_status.json'

targets = [
    r'C:\Users\Strong Baesus PC1\OneDrive\Desktop',
    r'C:\Users\Strong Baesus PC1\Downloads'
]

for t in targets:
    if os.path.exists(t):
        prompt_dst = os.path.join(t, 'MISSION_PROMPT.md')
        arch_dst = os.path.join(t, 'ARCHITECTURE.md')
        shutil.copy2(src_prompt, prompt_dst)
        shutil.copy2(src_arch, arch_dst)
        
        # Create ZIP bundle
        zip_path = os.path.join(t, 'cbot_cloud_resource_bundle.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(src_prompt, 'MISSION_PROMPT.md')
            zf.write(src_arch, 'ARCHITECTURE.md')
            if os.path.exists(src_btest):
                zf.write(src_btest, 'backtest_data.json')
            if os.path.exists(src_live):
                zf.write(src_live, 'live_status.json')
        print("Successfully prepared files in:", t)
        print("  1. MISSION_PROMPT.md:", round(os.path.getsize(prompt_dst)/1024, 1), "KB")
        print("  2. ARCHITECTURE.md:", round(os.path.getsize(arch_dst)/1024, 1), "KB")
        print("  3. cbot_cloud_resource_bundle.zip:", round(os.path.getsize(zip_path)/1024, 1), "KB")
