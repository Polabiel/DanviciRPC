import os
candidates = [
    '/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules',
    r'C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules',
    '/opt/resolve/libs/Fusion/',
]
for p in candidates:
    print(p, os.path.isdir(p))
