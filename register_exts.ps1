$vbs   = 'C:\Users\toyuv\AppData\Local\TinyTalk\launch.vbs'
$cmd   = 'wscript.exe "' + $vbs + '" "%1"'
$label = 'Transcribe with TinyTalk'
$exts  = @('mp4','mkv','mov','avi','wmv','m4v','webm','flv','ts','mts','m2ts',
           'mpg','mpeg','3gp','ogv','mp3','wav','flac','aac','ogg','m4a','wma',
           'opus','aiff','aif')

foreach ($e in $exts) {
    $base = "HKCU:\Software\Classes\SystemFileAssociations\.$e\shell\TinyTalk"
    New-Item -Path $base -Force | Out-Null
    Set-ItemProperty -Path $base -Name '(default)' -Value $label
    New-Item -Path "$base\command" -Force | Out-Null
    Set-ItemProperty -Path "$base\command" -Name '(default)' -Value $cmd
    Write-Host "  registered .$e"
}
Write-Host "Done"
