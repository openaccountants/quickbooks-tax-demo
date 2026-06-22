# VHS tape — renders an animated GIF of the demo.
#   brew install vhs   (https://github.com/charmbracelet/vhs)
#   vhs demo.tape      -> demo.gif

Output demo.gif

Set FontSize 16
Set Width 1280
Set Height 820
Set Theme "Github Dark"
Set Padding 20

Type "python pipeline.py"
Enter
Sleep 4s
