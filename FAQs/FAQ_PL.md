# FAQ (Najczęściej Zadawane Pytania)

[🇺🇸 English FAQ](FAQ_EN.md) | [🇷🇺 ЧаВо на Русском](FAQ_RU.md) | [🇮🇹 FAQ in Italiano](FAQ_IT.md) | [✓] 🇵🇱 FAQ po Polsku

> [!WARNING]
> This FAQ documents the retired YTLite-based build. See the [current platform support and build instructions](../README.md).

<details>
  <summary>Jakie wersje iOS obsługuje YouTube Plus?</summary>
    <p>YouTube Plus obsługuje iOS 14 i nowsze. <strong>Jednakże</strong>, jeśli instalujesz go metodą sideload na urządzeniu bez jailbreaka, musisz również wziąć pod uwagę kompatybilność aplikacji YouTube z Twoją wersją iOS. Poniżej znajduje się lista ostatnich obsługiwanych wersji YouTube dla poszczególnych wersji iOS:</p>
    <li><strong>iOS 14</strong>: YouTube v19.20.2</li>
    <li><strong>iOS 15</strong>: YouTube v20.21.6</li>
    <li><strong>iOS 16+</strong>: Dowolna wersja, zgodna z obsługą przez YouTube</li>
</details>
<br>
<details>
  <summary>Moja wersja iOS nie jest już obsługiwana przez najnowszą aplikację YouTube. Co mogę zrobić?</summary>
    <p>Oto kilka możliwych opcji:</p>
    <li><a href="https://ios.cfw.guide/get-started/">Zrób jailbreak urządzenia</a>, zainstaluj ostatnią obsługiwaną wersję YouTube ze sklepu App Store i <a href="http://dvntm0.github.io/#jb">zainstaluj YouTube Plus jako tweak</a></li>
    <li><a href="https://ios.cfw.guide/installing-trollstore/">Zainstaluj TrollStore</a>, następnie <a href="https://github.com/Lessica/TrollFools/releases/">TrollFools</a>, zainstaluj ostatnią obsługiwaną wersję YouTube ze sklepu App Store i wstrzyknij <a href="https://github.com/dayanch96/YTLite/releases/">YouTube Plus</a> przy użyciu TrollFools</li>
    <li>Znajdź kompatybilną wersję IPA w internecie i <a href="../README.md#how-to-build-a-youtube-plus-app-using-github-actions">zbuduj aplikację YouTube Plus przy użyciu GitHub Actions</a></li>
</details>
<br>
<details>
  <summary>Przestało działać przesyłanie (Cast) w zainstalowanym metodą sideload YouTube Plus. Co powinienem zrobić?</summary>
    <p>Do czasu rozwiązania problemu zaleca się korzystanie z wersji YouTube 20.14.1 lub starszej.</p>
</details>
<br>
<details>
  <summary>Podczas próby odtworzenia filmu pojawia się komunikat <strong><em>Coś poszło nie tak. Odśwież i spróbuj ponownie później.</em></strong></summary>
    <p>Zanim wyciągniesz wnioski, wyjaśnijmy kilka rzeczy:</p>
    <ol>
      <li><strong>To NIE jest</strong> spowodowane blokowaniem reklam</li>
      <li><strong>To NIE jest</strong> spowodowane rzekomym oznaczeniem Twojego konta</li>
      <li><strong>To NIE jest</strong> spowodowane ukrytym umieszczeniem Twojego konta na czarnej liście</li>
    </ol>
    <br>
    <p>Problem wydaje się tkwić w samym procesie sideloadingu, nawet bez zastosowania jakichkolwiek tweaków. Może być on związany z nieprawidłowym lub brakującym VisitorID lub VisitorData, jak zasugerowano <a href="https://github.com/pepeloni-away/userscripts/issues/6#issuecomment-2860641610">tutaj</a>. Błąd ten występuje częściej z powodu zaostrzenia zabezpieczeń anty-pobieraniowych przez YouTube.</p>
    <br>
    <p><strong>Możliwe tymczasowe obejście:</strong></p>
    <ol>
      <li>Całkowicie wyloguj się z obecnego konta (lub wszystkich kont): Przejdź do zakładki <em>Ty → Zmień konto → Zarządzaj kontami na tym urządzeniu → Usuń z tego urządzenia</em></li>
      <li>Obejrzyj kilka pełnometrażowych filmów bez logowania się. Pozostań wylogowany przez kilka godzin.</li>
      <li>Zaloguj się ponownie na konto, na którym występował problem</li>
    </ol>
</details>
