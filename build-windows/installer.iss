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
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Messages]
english.SetupAppRunningError=Setup has detected that %1 is currently running.%n%nPlease quit it (right-click its icon in the notification area, near the clock, and choose Quit), then click OK to continue, or Cancel to exit.
english.UninstallAppRunningError=%1 is currently running.%n%nPlease quit it (right-click its icon in the notification area, near the clock, and choose Quit), then click OK to continue, or Cancel to exit.

[CustomMessages]
english.AutoStart=Start {#AppName} when I sign in to Windows (it stays in the notification area)
english.OptionsGroup=Options:
english.DeleteData=Do you also want to delete your YT Grabber settings and the tools it downloaded (ffmpeg)?%n%n%1%n%nThe music and videos you downloaded are never deleted.
italian.AutoStart=Avvia {#AppName} all'accesso a Windows (resta nell'area di notifica)
italian.OptionsGroup=Opzioni:
italian.DeleteData=Vuoi eliminare anche le impostazioni di YT Grabber e gli strumenti scaricati (ffmpeg)?%n%n%1%n%nLa musica e i video che hai scaricato non vengono mai eliminati.
spanish.AutoStart=Iniciar {#AppName} al iniciar sesión en Windows (permanece en el área de notificación)
spanish.OptionsGroup=Opciones:
spanish.DeleteData=¿Quieres eliminar también los ajustes de YT Grabber y las herramientas que descargó (ffmpeg)?%n%n%1%n%nLa música y los vídeos que descargaste nunca se eliminan.
french.AutoStart=Démarrer {#AppName} à l'ouverture de session Windows (il reste dans la zone de notification)
french.OptionsGroup=Options :
french.DeleteData=Voulez-vous aussi supprimer les réglages de YT Grabber et les outils qu'il a téléchargés (ffmpeg) ?%n%n%1%n%nLa musique et les vidéos que vous avez téléchargées ne sont jamais supprimées.
german.AutoStart={#AppName} beim Anmelden bei Windows starten (bleibt im Infobereich)
german.OptionsGroup=Optionen:
german.DeleteData=Möchten Sie auch die Einstellungen von YT Grabber und die heruntergeladenen Werkzeuge (ffmpeg) löschen?%n%n%1%n%nDie heruntergeladene Musik und die Videos werden nie gelöscht.
brazilianportuguese.AutoStart=Iniciar o {#AppName} ao entrar no Windows (ele fica na área de notificação)
brazilianportuguese.OptionsGroup=Opções:
brazilianportuguese.DeleteData=Deseja excluir também as configurações do YT Grabber e as ferramentas que ele baixou (ffmpeg)?%n%n%1%n%nAs músicas e os vídeos que você baixou nunca são excluídos.
dutch.AutoStart={#AppName} starten wanneer ik me aanmeld bij Windows (blijft in het systeemvak)
dutch.OptionsGroup=Opties:
dutch.DeleteData=Wilt u ook uw YT Grabber-instellingen en de gedownloade hulpmiddelen (ffmpeg) verwijderen?%n%n%1%n%nDe muziek en video's die u hebt gedownload worden nooit verwijderd.
polish.AutoStart=Uruchamiaj {#AppName} po zalogowaniu do Windows (pozostaje w obszarze powiadomień)
polish.OptionsGroup=Opcje:
polish.DeleteData=Czy usunąć także ustawienia YT Grabber i pobrane narzędzia (ffmpeg)?%n%n%1%n%nPobrana muzyka i filmy nigdy nie są usuwane.
russian.AutoStart=Запускать {#AppName} при входе в Windows (остаётся в области уведомлений)
russian.OptionsGroup=Параметры:
russian.DeleteData=Удалить также настройки YT Grabber и загруженные им инструменты (ffmpeg)?%n%n%1%n%nСкачанные вами музыка и видео никогда не удаляются.
turkish.AutoStart=Windows'ta oturum açtığımda {#AppName} başlasın (bildirim alanında kalır)
turkish.OptionsGroup=Seçenekler:
turkish.DeleteData=YT Grabber ayarlarını ve indirdiği araçları (ffmpeg) da silmek istiyor musunuz?%n%n%1%n%nİndirdiğiniz müzik ve videolar asla silinmez.
arabic.AutoStart=تشغيل {#AppName} عند تسجيل الدخول إلى Windows (يبقى في منطقة الإشعارات)
arabic.OptionsGroup=خيارات:
arabic.DeleteData=هل تريد أيضًا حذف إعدادات YT Grabber والأدوات التي نزّلها (ffmpeg)؟%n%n%1%n%nلا تُحذف الموسيقى ومقاطع الفيديو التي نزّلتها أبدًا.
japanese.AutoStart=Windows にサインインしたとき {#AppName} を起動する（通知領域に常駐します）
japanese.OptionsGroup=オプション:
japanese.DeleteData=YT Grabber の設定とダウンロードされたツール（ffmpeg）も削除しますか？%n%n%1%n%nダウンロードした音楽や動画は削除されません。
korean.AutoStart=Windows에 로그인할 때 {#AppName} 시작(알림 영역에 상주)
korean.OptionsGroup=옵션:
korean.DeleteData=YT Grabber 설정과 다운로드된 도구(ffmpeg)도 삭제하시겠습니까?%n%n%1%n%n다운로드한 음악과 동영상은 삭제되지 않습니다.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart"; Description: "{cm:AutoStart}"; GroupDescription: "{cm:OptionsGroup}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#LicenseFile}"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#AppName}"; ValueData: """{app}\{#AppExe}"" --background"; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

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
      if MsgBox(FmtMessage(CustomMessage('DeleteData'), [DataDir]), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        DelTree(DataDir, True, True, True);
  end;
end;
