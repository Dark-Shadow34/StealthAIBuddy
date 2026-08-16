Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Check if compiled EXE exists in dist
exePath = scriptDir & "\dist\DesktopWindowHelper.exe"

If fso.FileExists(exePath) Then
    WshShell.Run """" & exePath & """", 0, False
Else
    WshShell.Run "pythonw.exe """ & scriptDir & "\main.py""", 0, False
End If
