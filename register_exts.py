import winreg

VBS   = r'C:\Users\toyuv\AppData\Local\TinyTalk\launch.vbs'
CMD   = f'wscript.exe "{VBS}" "%1"'
LABEL = 'Transcribe with TinyTalk'

EXTS = [
    'mp4','mkv','mov','avi','wmv','m4v','webm','flv','ts','mts','m2ts',
    'mpg','mpeg','3gp','ogv',
    'mp3','wav','flac','aac','ogg','m4a','wma','opus','aiff','aif',
]

for e in EXTS:
    base = rf'Software\Classes\SystemFileAssociations\.{e}\shell\TinyTalk'
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, base) as k:
        winreg.SetValueEx(k, '', 0, winreg.REG_SZ, LABEL)
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, base + r'\command') as k:
        winreg.SetValueEx(k, '', 0, winreg.REG_SZ, CMD)
    print(f'  registered .{e}')

print('Done')
