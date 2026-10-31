"""Texts of the Windows shell (tray menu, start-up window, message boxes) in the languages of the interface.

The language is the one chosen in the web interface (saved in settings.json); until one is chosen, the language of
Windows is used. English is the fallback for every missing language or text.
"""
import ctypes
import json
import os

CODES = ('en', 'it', 'es', 'fr', 'de', 'pt', 'nl', 'pl', 'ru', 'tr', 'ar', 'hi', 'id', 'zh', 'ja', 'ko')

TEXTS = {
    'en': {
        'tray.open': 'Open YT Grabber', 'tray.folder': 'Open downloads folder', 'tray.quit': 'Quit',
        'quit.confirm': 'Downloads are still in progress.\n\nQuit anyway? Unfinished downloads can be resumed the next time you open YT Grabber.',
        'stopped': 'YT Grabber stopped unexpectedly. Details are in the log file in\n{log}',
        'tip.busy': 'YT Grabber - {a} downloading, {w} waiting',
        'splash.first': 'First start: downloading the tools needed for conversions.\nThis happens only once.',
        'splash.first.text': 'Preparing YT Grabber for the first time...',
        'splash.start': 'Starting the program...', 'splash.start.text': 'Starting YT Grabber...',
        'err.start': 'YT Grabber could not start. Details are in the log file in\n{log}',
        'warn.ffmpeg': 'YT Grabber could not download ffmpeg, which it needs to convert audio and video.\n\nCheck your Internet connection. The program works, but conversions will fail until ffmpeg is installed: quit it from the tray icon and open it again to retry.',
        'err.fatal': 'YT Grabber hit an error and has to close.',
    },
    'it': {
        'tray.open': 'Apri YT Grabber', 'tray.folder': 'Apri la cartella dei download', 'tray.quit': 'Esci',
        'quit.confirm': 'Ci sono ancora download in corso.\n\nUscire comunque? I download non finiti si possono riprendere alla prossima apertura di YT Grabber.',
        'stopped': 'YT Grabber si è fermato in modo imprevisto. I dettagli sono nel file di log in\n{log}',
        'tip.busy': 'YT Grabber - {a} in download, {w} in attesa',
        'splash.first': 'Primo avvio: scarico gli strumenti necessari per le conversioni.\nSuccede una volta sola.',
        'splash.first.text': 'Preparo YT Grabber per la prima volta...',
        'splash.start': 'Avvio del programma...', 'splash.start.text': 'Avvio di YT Grabber...',
        'err.start': 'YT Grabber non è riuscito ad avviarsi. I dettagli sono nel file di log in\n{log}',
        'warn.ffmpeg': 'YT Grabber non è riuscito a scaricare ffmpeg, che serve per convertire audio e video.\n\nControlla la connessione a Internet. Il programma funziona, ma le conversioni falliranno finché ffmpeg non è installato: chiudilo dall\'icona nell\'area di notifica e riaprilo per riprovare.',
        'err.fatal': 'YT Grabber ha incontrato un errore e deve chiudersi.',
    },
    'es': {
        'tray.open': 'Abrir YT Grabber', 'tray.folder': 'Abrir la carpeta de descargas', 'tray.quit': 'Salir',
        'quit.confirm': 'Aún hay descargas en curso.\n\n¿Salir de todos modos? Las descargas sin terminar se pueden reanudar la próxima vez que abras YT Grabber.',
        'stopped': 'YT Grabber se detuvo de forma inesperada. Los detalles están en el archivo de registro en\n{log}',
        'tip.busy': 'YT Grabber - {a} descargando, {w} en espera',
        'splash.first': 'Primer inicio: descargando las herramientas necesarias para las conversiones.\nEsto ocurre solo una vez.',
        'splash.first.text': 'Preparando YT Grabber por primera vez...',
        'splash.start': 'Iniciando el programa...', 'splash.start.text': 'Iniciando YT Grabber...',
        'err.start': 'YT Grabber no pudo iniciarse. Los detalles están en el archivo de registro en\n{log}',
        'warn.ffmpeg': 'YT Grabber no pudo descargar ffmpeg, que necesita para convertir audio y vídeo.\n\nComprueba tu conexión a Internet. El programa funciona, pero las conversiones fallarán hasta que ffmpeg esté instalado: ciérralo desde el icono del área de notificación y ábrelo de nuevo para reintentar.',
        'err.fatal': 'YT Grabber encontró un error y debe cerrarse.',
    },
    'fr': {
        'tray.open': 'Ouvrir YT Grabber', 'tray.folder': 'Ouvrir le dossier des téléchargements', 'tray.quit': 'Quitter',
        'quit.confirm': 'Des téléchargements sont encore en cours.\n\nQuitter quand même ? Les téléchargements inachevés pourront être repris à la prochaine ouverture de YT Grabber.',
        'stopped': 'YT Grabber s\'est arrêté de façon inattendue. Les détails sont dans le fichier journal dans\n{log}',
        'tip.busy': 'YT Grabber - {a} en téléchargement, {w} en attente',
        'splash.first': 'Premier démarrage : téléchargement des outils nécessaires aux conversions.\nCela n\'arrive qu\'une seule fois.',
        'splash.first.text': 'Préparation de YT Grabber pour la première fois...',
        'splash.start': 'Démarrage du programme...', 'splash.start.text': 'Démarrage de YT Grabber...',
        'err.start': 'YT Grabber n\'a pas pu démarrer. Les détails sont dans le fichier journal dans\n{log}',
        'warn.ffmpeg': 'YT Grabber n\'a pas pu télécharger ffmpeg, dont il a besoin pour convertir l\'audio et la vidéo.\n\nVérifiez votre connexion Internet. Le programme fonctionne, mais les conversions échoueront tant que ffmpeg n\'est pas installé : quittez-le depuis l\'icône de la zone de notification puis rouvrez-le pour réessayer.',
        'err.fatal': 'YT Grabber a rencontré une erreur et doit se fermer.',
    },
    'de': {
        'tray.open': 'YT Grabber öffnen', 'tray.folder': 'Download-Ordner öffnen', 'tray.quit': 'Beenden',
        'quit.confirm': 'Es laufen noch Downloads.\n\nTrotzdem beenden? Unfertige Downloads können beim nächsten Öffnen von YT Grabber fortgesetzt werden.',
        'stopped': 'YT Grabber wurde unerwartet beendet. Details stehen in der Protokolldatei in\n{log}',
        'tip.busy': 'YT Grabber - {a} werden geladen, {w} warten',
        'splash.first': 'Erster Start: Die für Konvertierungen nötigen Werkzeuge werden heruntergeladen.\nDas geschieht nur einmal.',
        'splash.first.text': 'YT Grabber wird zum ersten Mal vorbereitet...',
        'splash.start': 'Das Programm wird gestartet...', 'splash.start.text': 'YT Grabber wird gestartet...',
        'err.start': 'YT Grabber konnte nicht starten. Details stehen in der Protokolldatei in\n{log}',
        'warn.ffmpeg': 'YT Grabber konnte ffmpeg nicht herunterladen, das zum Konvertieren von Audio und Video nötig ist.\n\nPrüfe deine Internetverbindung. Das Programm funktioniert, aber Konvertierungen schlagen fehl, bis ffmpeg installiert ist: Beende es über das Symbol im Infobereich und öffne es erneut, um es noch einmal zu versuchen.',
        'err.fatal': 'In YT Grabber ist ein Fehler aufgetreten und das Programm muss geschlossen werden.',
    },
    'pt': {
        'tray.open': 'Abrir o YT Grabber', 'tray.folder': 'Abrir a pasta de downloads', 'tray.quit': 'Sair',
        'quit.confirm': 'Ainda há downloads em andamento.\n\nSair mesmo assim? Os downloads inacabados podem ser retomados na próxima vez que você abrir o YT Grabber.',
        'stopped': 'O YT Grabber parou inesperadamente. Os detalhes estão no arquivo de registro em\n{log}',
        'tip.busy': 'YT Grabber - {a} baixando, {w} aguardando',
        'splash.first': 'Primeiro início: baixando as ferramentas necessárias para as conversões.\nIsso acontece só uma vez.',
        'splash.first.text': 'Preparando o YT Grabber pela primeira vez...',
        'splash.start': 'Iniciando o programa...', 'splash.start.text': 'Iniciando o YT Grabber...',
        'err.start': 'O YT Grabber não conseguiu iniciar. Os detalhes estão no arquivo de registro em\n{log}',
        'warn.ffmpeg': 'O YT Grabber não conseguiu baixar o ffmpeg, de que precisa para converter áudio e vídeo.\n\nVerifique sua conexão com a Internet. O programa funciona, mas as conversões vão falhar até o ffmpeg ser instalado: feche-o pelo ícone na área de notificação e abra de novo para tentar outra vez.',
        'err.fatal': 'O YT Grabber encontrou um erro e precisa ser fechado.',
    },
    'nl': {
        'tray.open': 'YT Grabber openen', 'tray.folder': 'Downloadmap openen', 'tray.quit': 'Afsluiten',
        'quit.confirm': 'Er zijn nog downloads bezig.\n\nToch afsluiten? Onvoltooide downloads kunnen worden hervat als je YT Grabber de volgende keer opent.',
        'stopped': 'YT Grabber is onverwacht gestopt. Details staan in het logbestand in\n{log}',
        'tip.busy': 'YT Grabber - {a} downloaden, {w} wachten',
        'splash.first': 'Eerste start: de hulpmiddelen voor conversies worden gedownload.\nDit gebeurt maar één keer.',
        'splash.first.text': 'YT Grabber wordt voor het eerst voorbereid...',
        'splash.start': 'Het programma wordt gestart...', 'splash.start.text': 'YT Grabber wordt gestart...',
        'err.start': 'YT Grabber kon niet starten. Details staan in het logbestand in\n{log}',
        'warn.ffmpeg': 'YT Grabber kon ffmpeg niet downloaden, dat nodig is om audio en video te converteren.\n\nControleer je internetverbinding. Het programma werkt, maar conversies mislukken totdat ffmpeg is geïnstalleerd: sluit het af via het pictogram in het systeemvak en open het opnieuw om het nog eens te proberen.',
        'err.fatal': 'YT Grabber heeft een fout aangetroffen en moet worden gesloten.',
    },
    'pl': {
        'tray.open': 'Otwórz YT Grabber', 'tray.folder': 'Otwórz folder pobranych plików', 'tray.quit': 'Zakończ',
        'quit.confirm': 'Nadal trwają pobierania.\n\nZakończyć mimo to? Niedokończone pobierania można wznowić przy następnym otwarciu YT Grabber.',
        'stopped': 'YT Grabber nieoczekiwanie przestał działać. Szczegóły są w pliku dziennika w\n{log}',
        'tip.busy': 'YT Grabber - pobieranie: {a}, oczekuje: {w}',
        'splash.first': 'Pierwsze uruchomienie: pobieranie narzędzi potrzebnych do konwersji.\nTo dzieje się tylko raz.',
        'splash.first.text': 'Przygotowywanie YT Grabber po raz pierwszy...',
        'splash.start': 'Uruchamianie programu...', 'splash.start.text': 'Uruchamianie YT Grabber...',
        'err.start': 'YT Grabber nie mógł się uruchomić. Szczegóły są w pliku dziennika w\n{log}',
        'warn.ffmpeg': 'YT Grabber nie mógł pobrać ffmpeg, którego potrzebuje do konwersji dźwięku i wideo.\n\nSprawdź połączenie z Internetem. Program działa, ale konwersje będą zawodzić, dopóki ffmpeg nie zostanie zainstalowany: zamknij program z ikony w obszarze powiadomień i otwórz go ponownie, aby spróbować jeszcze raz.',
        'err.fatal': 'W YT Grabber wystąpił błąd i program musi zostać zamknięty.',
    },
    'ru': {
        'tray.open': 'Открыть YT Grabber', 'tray.folder': 'Открыть папку загрузок', 'tray.quit': 'Выход',
        'quit.confirm': 'Загрузки ещё выполняются.\n\nВсё равно выйти? Незавершённые загрузки можно будет продолжить при следующем открытии YT Grabber.',
        'stopped': 'YT Grabber неожиданно остановился. Подробности в файле журнала в\n{log}',
        'tip.busy': 'YT Grabber - загружается: {a}, ожидает: {w}',
        'splash.first': 'Первый запуск: загрузка инструментов, нужных для конвертации.\nЭто происходит только один раз.',
        'splash.first.text': 'Первая подготовка YT Grabber...',
        'splash.start': 'Запуск программы...', 'splash.start.text': 'Запуск YT Grabber...',
        'err.start': 'YT Grabber не удалось запустить. Подробности в файле журнала в\n{log}',
        'warn.ffmpeg': 'YT Grabber не удалось скачать ffmpeg, который нужен для конвертации аудио и видео.\n\nПроверьте подключение к Интернету. Программа работает, но конвертация не будет выполняться, пока ffmpeg не установлен: закройте её через значок в области уведомлений и откройте снова, чтобы повторить.',
        'err.fatal': 'В YT Grabber произошла ошибка, и программа будет закрыта.',
    },
    'tr': {
        'tray.open': 'YT Grabber\'ı aç', 'tray.folder': 'İndirme klasörünü aç', 'tray.quit': 'Çık',
        'quit.confirm': 'İndirmeler hâlâ sürüyor.\n\nYine de çıkılsın mı? Bitmemiş indirmeler YT Grabber\'ı bir sonraki açışınızda sürdürülebilir.',
        'stopped': 'YT Grabber beklenmedik şekilde durdu. Ayrıntılar şu konumdaki günlük dosyasındadır:\n{log}',
        'tip.busy': 'YT Grabber - {a} indiriliyor, {w} bekliyor',
        'splash.first': 'İlk başlatma: dönüştürmeler için gereken araçlar indiriliyor.\nBu yalnızca bir kez olur.',
        'splash.first.text': 'YT Grabber ilk kez hazırlanıyor...',
        'splash.start': 'Program başlatılıyor...', 'splash.start.text': 'YT Grabber başlatılıyor...',
        'err.start': 'YT Grabber başlatılamadı. Ayrıntılar şu konumdaki günlük dosyasındadır:\n{log}',
        'warn.ffmpeg': 'YT Grabber, ses ve videoyu dönüştürmek için gereken ffmpeg\'i indiremedi.\n\nİnternet bağlantınızı kontrol edin. Program çalışır, ancak ffmpeg kurulana kadar dönüştürmeler başarısız olur: bildirim alanındaki simgeden çıkın ve yeniden denemek için tekrar açın.',
        'err.fatal': 'YT Grabber bir hatayla karşılaştı ve kapanmak zorunda.',
    },
    'ar': {
        'tray.open': 'فتح YT Grabber', 'tray.folder': 'فتح مجلد التنزيلات', 'tray.quit': 'خروج',
        'quit.confirm': 'ما زالت هناك تنزيلات قيد التنفيذ.\n\nهل تريد الخروج على أي حال؟ يمكن استئناف التنزيلات غير المكتملة عند فتح YT Grabber في المرة القادمة.',
        'stopped': 'توقف YT Grabber بشكل غير متوقع. التفاصيل في ملف السجل في\n{log}',
        'tip.busy': 'YT Grabber - {a} قيد التنزيل، {w} في الانتظار',
        'splash.first': 'التشغيل الأول: جارٍ تنزيل الأدوات اللازمة للتحويلات.\nيحدث هذا مرة واحدة فقط.',
        'splash.first.text': 'جارٍ تجهيز YT Grabber لأول مرة...',
        'splash.start': 'جارٍ تشغيل البرنامج...', 'splash.start.text': 'جارٍ تشغيل YT Grabber...',
        'err.start': 'تعذّر تشغيل YT Grabber. التفاصيل في ملف السجل في\n{log}',
        'warn.ffmpeg': 'تعذّر على YT Grabber تنزيل ffmpeg الذي يحتاجه لتحويل الصوت والفيديو.\n\nتحقق من اتصالك بالإنترنت. البرنامج يعمل لكن التحويلات ستفشل حتى يُثبَّت ffmpeg: أغلقه من الأيقونة في منطقة الإشعارات ثم افتحه مجددًا لإعادة المحاولة.',
        'err.fatal': 'واجه YT Grabber خطأً ويجب أن يُغلق.',
    },
    'hi': {
        'tray.open': 'YT Grabber खोलें', 'tray.folder': 'डाउनलोड फ़ोल्डर खोलें', 'tray.quit': 'बाहर निकलें',
        'quit.confirm': 'डाउनलोड अभी जारी हैं।\n\nफिर भी बाहर निकलें? अधूरे डाउनलोड अगली बार YT Grabber खोलने पर फिर शुरू किए जा सकते हैं।',
        'stopped': 'YT Grabber अचानक रुक गया। विवरण इस लॉग फ़ाइल में है:\n{log}',
        'tip.busy': 'YT Grabber - {a} डाउनलोड हो रहे, {w} प्रतीक्षा में',
        'splash.first': 'पहली बार शुरू करना: रूपांतरण के लिए ज़रूरी टूल डाउनलोड हो रहे हैं।\nऐसा सिर्फ़ एक बार होता है।',
        'splash.first.text': 'YT Grabber को पहली बार तैयार किया जा रहा है...',
        'splash.start': 'प्रोग्राम शुरू हो रहा है...', 'splash.start.text': 'YT Grabber शुरू हो रहा है...',
        'err.start': 'YT Grabber शुरू नहीं हो सका। विवरण इस लॉग फ़ाइल में है:\n{log}',
        'warn.ffmpeg': 'YT Grabber ffmpeg डाउनलोड नहीं कर सका, जो ऑडियो और वीडियो बदलने के लिए ज़रूरी है।\n\nअपना इंटरनेट कनेक्शन जाँचें। प्रोग्राम चलता है, पर ffmpeg इंस्टॉल होने तक रूपांतरण विफल रहेंगे: इसे नोटिफ़िकेशन क्षेत्र के आइकन से बंद करें और दोबारा कोशिश के लिए फिर खोलें।',
        'err.fatal': 'YT Grabber में त्रुटि आई है और उसे बंद होना होगा।',
    },
    'id': {
        'tray.open': 'Buka YT Grabber', 'tray.folder': 'Buka folder unduhan', 'tray.quit': 'Keluar',
        'quit.confirm': 'Masih ada unduhan yang berjalan.\n\nTetap keluar? Unduhan yang belum selesai dapat dilanjutkan saat Anda membuka YT Grabber lagi.',
        'stopped': 'YT Grabber berhenti secara tak terduga. Detailnya ada di file log di\n{log}',
        'tip.busy': 'YT Grabber - {a} mengunduh, {w} menunggu',
        'splash.first': 'Pertama kali dijalankan: mengunduh alat yang diperlukan untuk konversi.\nIni hanya terjadi sekali.',
        'splash.first.text': 'Menyiapkan YT Grabber untuk pertama kali...',
        'splash.start': 'Memulai program...', 'splash.start.text': 'Memulai YT Grabber...',
        'err.start': 'YT Grabber tidak dapat dimulai. Detailnya ada di file log di\n{log}',
        'warn.ffmpeg': 'YT Grabber tidak dapat mengunduh ffmpeg, yang diperlukan untuk mengonversi audio dan video.\n\nPeriksa koneksi Internet Anda. Program tetap berfungsi, tetapi konversi akan gagal sampai ffmpeg terpasang: keluar dari ikon di area notifikasi lalu buka lagi untuk mencoba kembali.',
        'err.fatal': 'YT Grabber mengalami kesalahan dan harus ditutup.',
    },
    'zh': {
        'tray.open': '打开 YT Grabber', 'tray.folder': '打开下载文件夹', 'tray.quit': '退出',
        'quit.confirm': '仍有下载正在进行。\n\n仍要退出吗？未完成的下载可在下次打开 YT Grabber 时继续。',
        'stopped': 'YT Grabber 意外停止。详细信息见日志文件：\n{log}',
        'tip.busy': 'YT Grabber - {a} 个下载中，{w} 个等待中',
        'splash.first': '首次启动：正在下载转换所需的工具。\n此过程只会发生一次。',
        'splash.first.text': '正在首次准备 YT Grabber...',
        'splash.start': '正在启动程序...', 'splash.start.text': '正在启动 YT Grabber...',
        'err.start': 'YT Grabber 无法启动。详细信息见日志文件：\n{log}',
        'warn.ffmpeg': 'YT Grabber 无法下载 ffmpeg，而转换音频和视频需要它。\n\n请检查网络连接。程序仍可使用，但在安装 ffmpeg 之前转换会失败：请从通知区域图标退出程序，然后重新打开再试。',
        'err.fatal': 'YT Grabber 遇到错误，必须关闭。',
    },
    'ja': {
        'tray.open': 'YT Grabber を開く', 'tray.folder': 'ダウンロードフォルダーを開く', 'tray.quit': '終了',
        'quit.confirm': 'ダウンロードがまだ進行中です。\n\nそれでも終了しますか？未完了のダウンロードは、次に YT Grabber を開いたときに再開できます。',
        'stopped': 'YT Grabber が予期せず停止しました。詳細は次のログファイルにあります：\n{log}',
        'tip.busy': 'YT Grabber - ダウンロード中 {a} 件、待機中 {w} 件',
        'splash.first': '初回起動：変換に必要なツールをダウンロードしています。\nこれは 1 回だけ行われます。',
        'splash.first.text': 'YT Grabber を初めて準備しています...',
        'splash.start': 'プログラムを起動しています...', 'splash.start.text': 'YT Grabber を起動しています...',
        'err.start': 'YT Grabber を起動できませんでした。詳細は次のログファイルにあります：\n{log}',
        'warn.ffmpeg': 'YT Grabber は、音声と動画の変換に必要な ffmpeg をダウンロードできませんでした。\n\nインターネット接続を確認してください。プログラムは動作しますが、ffmpeg をインストールするまで変換は失敗します。通知領域のアイコンから終了し、もう一度開いて再試行してください。',
        'err.fatal': 'YT Grabber でエラーが発生したため、終了する必要があります。',
    },
    'ko': {
        'tray.open': 'YT Grabber 열기', 'tray.folder': '다운로드 폴더 열기', 'tray.quit': '종료',
        'quit.confirm': '다운로드가 아직 진행 중입니다.\n\n그래도 종료할까요? 끝나지 않은 다운로드는 다음에 YT Grabber를 열 때 이어서 받을 수 있습니다.',
        'stopped': 'YT Grabber가 예기치 않게 중지되었습니다. 자세한 내용은 다음 로그 파일에 있습니다:\n{log}',
        'tip.busy': 'YT Grabber - 다운로드 중 {a}개, 대기 중 {w}개',
        'splash.first': '처음 시작: 변환에 필요한 도구를 다운로드하는 중입니다.\n이 작업은 한 번만 수행됩니다.',
        'splash.first.text': 'YT Grabber를 처음으로 준비하는 중...',
        'splash.start': '프로그램을 시작하는 중...', 'splash.start.text': 'YT Grabber를 시작하는 중...',
        'err.start': 'YT Grabber를 시작할 수 없습니다. 자세한 내용은 다음 로그 파일에 있습니다:\n{log}',
        'warn.ffmpeg': 'YT Grabber가 오디오와 동영상 변환에 필요한 ffmpeg를 다운로드하지 못했습니다.\n\n인터넷 연결을 확인하세요. 프로그램은 동작하지만 ffmpeg를 설치하기 전까지 변환은 실패합니다. 알림 영역 아이콘에서 종료한 뒤 다시 열어 재시도하세요.',
        'err.fatal': 'YT Grabber에 오류가 발생하여 종료해야 합니다.',
    },
}

LOG_PATH = '%LOCALAPPDATA%\\YT-Grabber\\data\\logs\\app.log'


def windows_language():
    """The language of Windows as one of CODES ('en' if it is not one of them)."""
    try:
        buf = ctypes.create_unicode_buffer(85)
        ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 85)
        base = buf.value.lower().split('-')[0]
        return 'id' if base == 'in' else base if base in CODES else 'en'
    except Exception:
        return 'en'


def current_language(data_dir):
    """The language chosen in the web interface (settings.json); Windows' own language until one is chosen."""
    try:
        with open(os.path.join(data_dir, 'settings.json'), encoding='utf-8') as f:
            code = json.load(f).get('lang')
        if code in CODES:
            return code
    except Exception:
        pass
    return windows_language()


def text(data_dir, key, **values):
    table = TEXTS.get(current_language(data_dir), TEXTS['en'])
    s = table.get(key) or TEXTS['en'][key]
    values.setdefault('log', LOG_PATH)
    return s.format(**values)
