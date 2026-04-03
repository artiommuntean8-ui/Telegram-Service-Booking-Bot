# Telegram Booking Bot

Acesta este un bot de Telegram pentru programări, construit folosind Python și biblioteca **aiogram 3.x**. Botul permite utilizatorilor să își rezerve intervale orare, să își vadă programările și oferă o interfață administrativă pentru gestionarea tuturor înregistrărilor.

## 🚀 Funcționalități

*   **Sistem de Programare:** Utilizatorii pot alege data și ora dintr-o listă predefinită.
*   **Verificare Disponibilitate:** Intervalele orare deja ocupate sunt marcate și nu pot fi selectate din nou.
*   **Gestionare Programări:** Utilizatorii își pot vedea și anula propriile programări.
*   **Panou Admin:** Administratorul poate vizualiza toate programările și poate șterge orice intrare.
*   **Bază de date Asincronă:** Utilizează `aiosqlite` pentru a asigura performanța fără a bloca execuția botului.

## 🛠 Tehnologii utilizate

*   Python 3.8+
*   Aiogram 3 - Framework-ul pentru Telegram Bot.
*   Aiosqlite - Bază de date SQL asincronă.
*   Python-dotenv - Pentru gestionarea variabilelor de mediu.

## 📋 Cerințe

1.  Python instalat pe sistemul tău.
2.  Un token de bot obținut de la @BotFather.
3.  ID-ul tău de Telegram pentru accesul la panoul de admin.

## 🔧 Instalare și Configurare

1.  **Clonează repository-ul:**
    ```bash
    git clone <url-repository>
    cd "Bot bing registrations"
    ```

2.  **Instalează dependențele:**
    ```bash
    pip install aiogram aiosqlite python-dotenv
    ```

3.  **Configurează variabilele de mediu:**
    Creează un fișier `.env` în folderul rădăcină și adaugă următoarele date:
    ```env
    BOT_TOKEN=tokenul_tau_aici
    ADMIN_ID=id_ul_tau_de_telegram
    ```

## 🏃 Execuție

Pentru a porni botul, rulează:

```bash
python main.py
```