# TermiSignal pro Android

Tento dokument popisuje plán pro vytvoření Android verze aplikace TermiSignal.

## Požadavky

- Android Studio
- Znalost Kotlin nebo Java
- Základní znalost Android vývoje

## Plánovaná architektura

Pro Android verzi budeme používat:

1. **Kotlin** jako hlavní programovací jazyk
2. **Jetpack Compose** pro UI
3. **Signal Protocol Library** pro end-to-end šifrování
4. **Room Database** pro lokální ukládání dat
5. **Retrofit** pro síťovou komunikaci
6. **Dagger Hilt** pro dependency injection

## Struktura projektu

```
app/
├── src/
│   ├── main/
│   │   ├── java/com/termisignal/
│   │   │   ├── ui/
│   │   │   │   ├── theme/
│   │   │   │   ├── login/
│   │   │   │   ├── chat/
│   │   │   ├── data/
│   │   │   │   ├── repository/
│   │   │   │   ├── local/
│   │   │   │   ├── remote/
│   │   │   ├── domain/
│   │   │   │   ├── model/
│   │   │   │   ├── usecase/
│   │   │   ├── crypto/
│   │   │   │   ├── SignalProtocolImplementation.kt
│   │   │   ├── di/
│   │   │   ├── MainActivity.kt
│   │   │   ├── TermiSignalApplication.kt
│   │   ├── res/
│   │   ├── AndroidManifest.xml
│   ├── test/
│   ├── androidTest/
├── build.gradle
```

## UI Design

Android verze bude zachovávat terminálový vzhled, ale bude optimalizována pro mobilní zařízení:

1. Černé pozadí
2. Barevné texty pro různé uživatele
3. Formát zpráv: `uživatel@něco: --- text ---`
4. Jednoduchá navigace mezi konverzacemi

## Implementace šifrování

Pro implementaci end-to-end šifrování budeme používat oficiální Signal Protocol Library:

```kotlin
implementation("org.signal:libsignal-protocol-java:2.8.1")
```

## Plán vývoje

1. Vytvoření základní struktury projektu
2. Implementace UI (přihlašovací obrazovka, chatovací obrazovka)
3. Implementace lokální databáze
4. Implementace šifrování
5. Implementace síťové komunikace
6. Testování a ladění
7. Vydání první verze

## Poznámky

- Android verze bude kompatibilní s desktopovou verzí
- Bude používat stejný protokol pro komunikaci
- Bude podporovat stejné funkce jako desktopová verze
