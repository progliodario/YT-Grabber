; Inno Setup script (https://jrsoftware.org/isinfo.php) for the YT Grabber installer.
; build_windows.py passes the version, the paths and the output folder with /D options.
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#ifndef SourceDir
  #error SourceDir is not defined (run build-windows\build-windows.bat)
#endif
#define AppName "YT Grabber"
#define AppExe "YT-Grabber.exe"

[Setup]
AppId={{B7D5E0B2-4E4B-4C55-9B3A-6D3E8A2F9C11}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=progliodario
AppPublisherURL=https://github.com/progliodario/YT-Grabber
AppSupportURL=https://github.com/progliodario/YT-Grabber/issues
AppUpdatesURL=https://github.com/progliodario/YT-Grabber/releases
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppName} setup
DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes
; Installs for the current user (no administrator prompt); the wizard offers "for all users" as an option
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={#OutDir}
OutputBaseFilename=YT-Grabber-Setup-{#AppVersion}
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
LicenseFile={#LicenseFile}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
; The running program creates this mutex: Setup and the uninstaller ask the user to quit it first
AppMutex=YT-Grabber-Running
CloseApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
SetupAppRunningError=Setup has detected that %1 is currently running.%n%nPlease quit it (right-click its icon in the notification area, near the clock, and choose Quit), then click OK to continue, or Cancel to exit.
UninstallAppRunningError=%1 is currently running.%n%nPlease quit it (right-click its icon in the notification area, near the clock, and choose Quit), then click OK to continue, or Cancel to exit.

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "autostart"; Description: "Start {#AppName} when I sign in to Windows (it stays in the notification area)"; GroupDescription: "Options:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#LicenseFile}"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#AppName}"; ValueData: """{app}\{#AppExe}"" --background"; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{localappdata}\YT-Grabber');
    // Settings, the download list and the downloaded tools (ffmpeg, about 200 MB) are kept unless the user agrees
    if DirExists(DataDir) and (not UninstallSilent) then
      if MsgBox('Do you also want to delete your YT Grabber settings and the tools it downloaded (ffmpeg)?' + #13#10#13#10 +
                DataDir + #13#10#13#10 + 'The music and videos you downloaded are never deleted.',
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        DelTree(DataDir, True, True, True);
  end;
end;
