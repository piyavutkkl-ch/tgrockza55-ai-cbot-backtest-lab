import os, json, sys

sys.stdout.reconfigure(encoding='utf-8')

convs = {
    'cbot_Data PAPER': '066c0b89-502c-4b32-b8ff-2f8201902c09',
    'cbot_Front-end UI': 'e652e0c3-4ea1-4562-92ed-d8d6ee9156b6',
    'cbot_Multi-Agent': '9ff7951d-7291-4be6-bea0-fc6a3c4e2aa8',
}

base_brain = r'C:\Users\Strong Baesus PC1\.gemini\antigravity\brain'

for name, cid in convs.items():
    p = os.path.join(base_brain, cid)
    print(f"\n=======================================================")
    print(f"CONVERSATION: {name} ({cid})")
    print(f"=======================================================")
    
    # List brain files
    if os.path.exists(p):
        for f in os.listdir(p):
            fp = os.path.join(p, f)
            if os.path.isfile(fp) and f.endswith(('.md', '.json', '.html', '.txt')):
                print(f"  Artifact: {f} ({os.path.getsize(fp)/1024:.1f} KB)")
                
    # Search for files edited/written in transcript
    trans = os.path.join(p, '.system_generated', 'logs', 'transcript.jsonl')
    touched_files = set()
    if os.path.exists(trans):
        with open(trans, 'r', encoding='utf-8') as f:
            for line in f:
                d = json.loads(line)
                for tc in d.get('tool_calls', []):
                    args = tc.get('args', {})
                    if 'Path' in args:
                        touched_files.add(args['Path'])
                    if 'CommandLine' in args:
                        cmd = args['CommandLine']
                        for token in cmd.split():
                            if ('\\' in token or '/' in token) and ('.py' in token or '.json' in token or '.html' in token or '.md' in token):
                                touched_files.add(token.strip('"\''))
    print(f"  Touched/Created Files ({len(touched_files)} files):")
    for tf in sorted(touched_files)[:15]:
        print(f"    - {tf}")
