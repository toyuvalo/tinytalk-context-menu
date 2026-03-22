# make-screenshots.ps1 -- Generate README screenshots for TinyTalk
# Builds mock forms matching the real app and captures with CopyFromScreen.

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$here   = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$outDir = Join-Path $here "screenshots"
New-Item -Path $outDir -ItemType Directory -Force | Out-Null

# Palette (matches tinytalk.py)
$cBg      = [System.Drawing.Color]::FromArgb(9,   9,   9  )
$cCard    = [System.Drawing.Color]::FromArgb(16,  16,  16 )
$cBorder  = [System.Drawing.Color]::FromArgb(31,  31,  31 )
$cAccent  = [System.Drawing.Color]::FromArgb(0,   217, 217)
$cText    = [System.Drawing.Color]::FromArgb(240, 240, 240)
$cDim     = [System.Drawing.Color]::FromArgb(58,  58,  58 )
$cMid     = [System.Drawing.Color]::FromArgb(102, 102, 102)
$cSuccess = [System.Drawing.Color]::FromArgb(0,   232, 122)
$cYellow  = [System.Drawing.Color]::FromArgb(255, 196, 0  )

function F($size, $bold=$false) {
    $style = if ($bold) { [System.Drawing.FontStyle]::Bold } else { [System.Drawing.FontStyle]::Regular }
    New-Object System.Drawing.Font('Consolas', $size, $style)
}

function Lbl($text, $x, $y, $w, $h, $color, $fsize=8, $bold=$false) {
    $l = New-Object System.Windows.Forms.Label
    $l.Text = $text
    $l.Location = New-Object System.Drawing.Point($x, $y)
    $l.Size = New-Object System.Drawing.Size($w, $h)
    $l.ForeColor = $color
    $l.Font = F $fsize $bold
    $l.BackColor = [System.Drawing.Color]::Transparent
    $l
}

function HRule($form, $y) {
    $p = New-Object System.Windows.Forms.Panel
    $p.Location = New-Object System.Drawing.Point(28, $y)
    $p.Size = New-Object System.Drawing.Size(404, 1)
    $p.BackColor = $cBorder
    $form.Controls.Add($p)
}

function Capture-Form($Form, $Path) {
    $Form.Show()
    $Form.BringToFront()
    [System.Windows.Forms.Application]::DoEvents()
    Start-Sleep -Milliseconds 400
    [System.Windows.Forms.Application]::DoEvents()
    $loc = $Form.Location
    $bmp = New-Object System.Drawing.Bitmap($Form.Width, $Form.Height)
    $g   = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($loc.X, $loc.Y, 0, 0, (New-Object System.Drawing.Size($Form.Width, $Form.Height)))
    $g.Dispose()
    $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    $Form.Close()
    $Form.Dispose()
    [System.Windows.Forms.Application]::DoEvents()
}

function Base-Form($title, $w, $h) {
    $f = New-Object System.Windows.Forms.Form
    $f.Text = $title
    $f.Size = New-Object System.Drawing.Size($w, $h)
    $f.StartPosition = 'CenterScreen'
    $f.FormBorderStyle = 'FixedSingle'
    $f.MaximizeBox = $false
    $f.BackColor = $cBg
    $f.ForeColor = $cText
    $f.TopMost = $true
    $f
}

# SCREENSHOT 1: Installer — all steps complete
function New-InstallerForm {
    $f = Base-Form 'TinyTalk -- Setup' 460 470
    $f.Controls.Add((Lbl 'TinyTalk' 28 26 160 34 $cAccent 20 $true))
    $f.Controls.Add((Lbl 'context menu installer' 150 36 240 16 $cMid 7))
    $f.Controls.Add((Lbl '-> C:\Users\...\AppData\Local\TinyTalk' 150 50 280 14 $cDim 7))
    HRule $f 80

    $steps = @(
        @{ icon='v'; text='Check Python';           color=$cSuccess }
        @{ icon='v'; text='Install faster-whisper'; color=$cSuccess }
        @{ icon='v'; text='Check ffmpeg';            color=$cSuccess }
        @{ icon='v'; text='Download Whisper model';  color=$cSuccess }
        @{ icon='v'; text='Copy files';              color=$cSuccess }
        @{ icon='v'; text='Register context menu';   color=$cSuccess }
    )
    $y = 100
    foreach ($s in $steps) {
        $f.Controls.Add((Lbl $s.icon 36 $y 18 22 $s.color 9 $true))
        $f.Controls.Add((Lbl $s.text 58 $y 340 22 $s.color 9))
        $y += 28
    }
    HRule $f 278

    $f.Controls.Add((Lbl 'TinyTalk installed!' 30 290 380 20 $cSuccess 8))

    $log = New-Object System.Windows.Forms.RichTextBox
    $log.Location = New-Object System.Drawing.Point(28, 318)
    $log.Size = New-Object System.Drawing.Size(404, 72)
    $log.BackColor = $cCard; $log.Font = F 8; $log.BorderStyle = 'None'; $log.ReadOnly = $true
    $log.AppendText("Right-click any audio or video file and choose:`n")
    $log.AppendText('"Transcribe with TinyTalk"')
    $log.SelectAll(); $log.SelectionColor = $cSuccess
    $f.Controls.Add($log)

    $btn = New-Object System.Windows.Forms.Button
    $btn.Text = 'CLOSE'; $btn.Location = New-Object System.Drawing.Point(28, 404)
    $btn.Size = New-Object System.Drawing.Size(404, 38); $btn.FlatStyle = 'Flat'
    $btn.FlatAppearance.BorderSize = 0; $btn.BackColor = $cSuccess; $btn.ForeColor = $cBg
    $btn.Font = F 10 $true; $f.Controls.Add($btn)
    $f
}

# SCREENSHOT 2: Transcribing — live speaker-labelled output mid-run
function New-TranscribingForm {
    $f = Base-Form 'TinyTalk' 520 470
    $f.Controls.Add((Lbl 'TinyTalk' 28 26 160 36 $cAccent 22 $true))
    $f.Controls.Add((Lbl 'whisper transcriber  /  model: base' 152 38 280 14 $cMid 7))
    $f.Controls.Add((Lbl '-> X:\TheBasementFiles\0_VIDEOS\moran' 152 50 280 14 $cDim 7))
    HRule $f 80

    $fbox = New-Object System.Windows.Forms.Panel
    $fbox.Location = New-Object System.Drawing.Point(28, 96)
    $fbox.Size = New-Object System.Drawing.Size(310, 28)
    $fbox.BackColor = $cCard; $f.Controls.Add($fbox)
    $f.Controls.Add((Lbl 'interview_recording.mp4' 38 100 290 20 $cText 9))

    HRule $f 132
    $f.Controls.Add((Lbl 'transcribing  [EN]  ~1m 12s left' 30 144 420 18 $cYellow 8))

    $pb = New-Object System.Windows.Forms.ProgressBar
    $pb.Location = New-Object System.Drawing.Point(28, 168)
    $pb.Size = New-Object System.Drawing.Size(464, 6)
    $pb.Style = 'Continuous'; $pb.Minimum = 0; $pb.Maximum = 100; $pb.Value = 34
    $f.Controls.Add($pb)

    $log = New-Object System.Windows.Forms.RichTextBox
    $log.Location = New-Object System.Drawing.Point(28, 182)
    $log.Size = New-Object System.Drawing.Size(464, 250)
    $log.BackColor = $cCard; $log.Font = F 8; $log.BorderStyle = 'None'; $log.ReadOnly = $true

    $entries = @(
        @{ c=$cDim;  t='  2 speakers detected' }
        @{ c=$cText; t='[0:00] SPEAKER 1: So the main issue we ran into' }
        @{ c=$cText; t='[0:03] SPEAKER 1: was the timeline shifting on us.' }
        @{ c=$cText; t='[0:06] SPEAKER 2: Right,' }
        @{ c=$cText; t='[0:07] SPEAKER 2: and that pushed everything back by a week.' }
        @{ c=$cText; t='[0:11] SPEAKER 1: Exactly.' }
        @{ c=$cText; t='[0:12] SPEAKER 1: So we had to reprioritise the deliverables.' }
        @{ c=$cText; t='[0:17] SPEAKER 2: Makes sense.' }
        @{ c=$cText; t='[0:18] SPEAKER 2: Did the client sign off on the new dates?' }
    )
    foreach ($e in $entries) {
        $s = $log.TextLength
        $log.AppendText($e.t + "`n")
        $log.Select($s, $e.t.Length)
        $log.SelectionColor = $e.c
    }
    $log.SelectionStart = $log.TextLength
    $f.Controls.Add($log)
    $f
}

# SCREENSHOT 3: Done — full transcript with OPEN TRANSCRIPT button
function New-DoneForm {
    $f = Base-Form 'TinyTalk' 520 470
    $f.Controls.Add((Lbl 'TinyTalk' 28 26 160 36 $cAccent 22 $true))
    $f.Controls.Add((Lbl 'whisper transcriber  /  model: base' 152 38 280 14 $cMid 7))
    $f.Controls.Add((Lbl '-> X:\TheBasementFiles\0_VIDEOS\moran' 152 50 280 14 $cDim 7))
    HRule $f 80

    $fbox = New-Object System.Windows.Forms.Panel
    $fbox.Location = New-Object System.Drawing.Point(28, 96)
    $fbox.Size = New-Object System.Drawing.Size(310, 28)
    $fbox.BackColor = $cCard; $f.Controls.Add($fbox)
    $f.Controls.Add((Lbl 'interview_recording.mp4' 38 100 290 20 $cText 9))

    HRule $f 132
    $f.Controls.Add((Lbl 'done  [EN]  ->  interview_recording.txt' 30 144 430 18 $cSuccess 8))

    $pb = New-Object System.Windows.Forms.ProgressBar
    $pb.Location = New-Object System.Drawing.Point(28, 168)
    $pb.Size = New-Object System.Drawing.Size(464, 6)
    $pb.Style = 'Continuous'; $pb.Minimum = 0; $pb.Maximum = 100; $pb.Value = 100
    $f.Controls.Add($pb)

    $log = New-Object System.Windows.Forms.RichTextBox
    $log.Location = New-Object System.Drawing.Point(28, 182)
    $log.Size = New-Object System.Drawing.Size(464, 198)
    $log.BackColor = $cCard; $log.Font = F 8; $log.BorderStyle = 'None'; $log.ReadOnly = $true

    $entries = @(
        @{ c=$cText;    t='[0:18] SPEAKER 2: Did the client sign off on the new dates?' }
        @{ c=$cText;    t='[0:22] SPEAKER 1: They did.' }
        @{ c=$cText;    t='[0:23] SPEAKER 1: We got approval yesterday afternoon.' }
        @{ c=$cText;    t='[0:27] SPEAKER 2: Perfect.' }
        @{ c=$cText;    t='[0:28] SPEAKER 2: Then we can lock the sprint for next Monday.' }
        @{ c=$cText;    t='[0:33] SPEAKER 1: Agreed.' }
        @{ c=$cSuccess; t='' }
        @{ c=$cSuccess; t='v  saved to: interview_recording.txt' }
    )
    foreach ($e in $entries) {
        $s = $log.TextLength
        $log.AppendText($e.t + "`n")
        $log.Select($s, $e.t.Length)
        $log.SelectionColor = $e.c
    }
    $log.SelectionStart = $log.TextLength
    $f.Controls.Add($log)

    $btn = New-Object System.Windows.Forms.Button
    $btn.Text = 'OPEN TRANSCRIPT'
    $btn.Location = New-Object System.Drawing.Point(28, 394)
    $btn.Size = New-Object System.Drawing.Size(464, 42)
    $btn.FlatStyle = 'Flat'; $btn.FlatAppearance.BorderSize = 0
    $btn.BackColor = $cAccent; $btn.ForeColor = $cBg; $btn.Font = F 9 $true
    $f.Controls.Add($btn)
    $f
}

# Run
Write-Host 'Generating screenshots...' -ForegroundColor Yellow
Capture-Form -Form (New-InstallerForm)    -Path (Join-Path $outDir 'installer.png')
Write-Host '  [1/3] installer.png' -ForegroundColor Green
Capture-Form -Form (New-TranscribingForm) -Path (Join-Path $outDir 'transcribing.png')
Write-Host '  [2/3] transcribing.png' -ForegroundColor Green
Capture-Form -Form (New-DoneForm)         -Path (Join-Path $outDir 'done.png')
Write-Host '  [3/3] done.png' -ForegroundColor Green
Write-Host ''
Write-Host "Done. Screenshots in: $outDir" -ForegroundColor Green
