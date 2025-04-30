# Mikroxizmatlar Arxitekturasi

Loyiha mikroxizmatlarga bo'linadi, har bir mikroxizmat ma'lum bir funksionallik uchun javobgar bo'ladi. Quyida mavjud modellarga asoslangan mikroxizmatlar va ularning vazifalari keltirilgan.

---

## Mikroxizmatlar

### 1. **Foydalanuvchilar Xizmati (Users Service)**
- **Vazifasi**: Foydalanuvchilarni boshqarish, ularning profillari va verifikatsiyasi.
- **Modellar**:
  - `User`
  - `VerificationCode`
- **API**:
  - Ro'yxatdan o'tish, avtorizatsiya, profilni boshqarish.
  - Kodlar orqali verifikatsiya qilish.

---

### 2. **Tariflar va Funksiyalar Xizmati (Tariffs Service)**
- **Vazifasi**: Tariflar, kategoriyalar, funksiyalar va chegirmalarni boshqarish.
- **Modellar**:
  - `TariffCategory`
  - `Tariff`
  - `Feature`
  - `TariffFeature`
  - `Sale`
- **API**:
  - Tariflar va kategoriyalar ro'yxatini olish.
  - Chegirmalar va funksiyalarni boshqarish.

---

### 3. **Testlar va Tahlillar Xizmati (Tests Service)**
- **Vazifasi**: Testlarni (tinglash, yozish, o'qish, gapirish va boshqalar) va ularning natijalarini boshqarish.
- **Modellar**:
  - `Listening`, `Writing`, `Speaking`, `Reading`, `Grammar`, `Vocabulary`, `Pronunciation` va ularning qismlari.
  - `ListeningAnalyse`, `WritingAnalyse`, `SpeakingAnalyse`, `ReadingAnalyse`, `GrammarAnalyse`, `VocabularyAnalyse`, `PronunciationAnalyse`.
- **API**:
  - Testlarni yaratish va boshqarish.
  - Natijalar va tahlillarni olish.

---

### 4. **Bildirishnomalar Xizmati (Notifications Service)**
- **Vazifasi**: Bildirishnomalarni va ularning holatini boshqarish.
- **Modellar**:
  - `Message`
  - `ReadStatus`
- **API**:
  - Bildirishnomalarni yuborish (pochta, sayt).
  - O'qilgan holatni kuzatish.

---

### 5. **To'lovlar va Tranzaksiyalar Xizmati (Payments and Transactions Service)**
- **Vazifasi**: To'lovlar va token tranzaksiyalarini boshqarish.
- **Modellar**:
  - `Payment`
  - `TokenTransaction`
- **API**:
  - To'lovlarni yaratish va boshqarish.
  - Token tranzaksiyalarini kuzatish.

---

## Mikroxizmatlar Arxitekturasi

```plaintext
+----------------------+       +-----------------------+
|  Users Service       |       |  Tariffs Service      |
|----------------------|       |-----------------------|
|  User               <--------> TariffCategory       |
|  VerificationCode   <--------> Tariff               |
|                      |       |  Feature             |
|                      |       |  TariffFeature       |
|                      |       |  Sale                |
+----------------------+       +-----------------------+

+----------------------+       +-----------------------+
|  Tests Service       |       |  Notifications Service|
|----------------------|       |-----------------------|
|  Listening           |       |  Message             |
|  Writing             |       |  ReadStatus          |
|  Speaking            |       |                       |
|  Reading             |       +-----------------------+
|  Grammar             |
|  Vocabulary          |
|  Pronunciation       |
|  Analyses            |
+----------------------+

+----------------------+
|  Payments Service    |
|----------------------|
|  Payment             |
|  TokenTransaction    |
+----------------------+
```

---

## Mikroxizmatlar O'rtasidagi O'zaro Aloqa

1. **Users Service**:
   - Foydalanuvchilarni boshqaradi.
   - Boshqa mikroxizmatlarga foydalanuvchilar haqidagi ma'lumotlarni taqdim etadi (masalan, tranzaksiyalar yoki bildirishnomalar uchun).

2. **Tariffs Service**:
   - Tariflar va funksiyalarni boshqaradi.
   - To'lovlar xizmati uchun tariflar haqidagi ma'lumotlarni taqdim etadi.

3. **Tests Service**:
   - Testlarni va tahlillarni boshqaradi.
   - Foydalanuvchilar haqidagi ma'lumotlarni olish uchun Users Service bilan o'zaro aloqa qiladi.

4. **Notifications Service**:
   - Foydalanuvchilarga bildirishnomalarni yuboradi.
   - Foydalanuvchilar haqidagi ma'lumotlarni Users Service'dan oladi.

5. **Payments Service**:
   - To'lovlar va tranzaksiyalarni boshqaradi.
   - Foydalanuvchilar haqidagi ma'lumotlarni Users Service'dan, tariflar haqidagi ma'lumotlarni Tariffs Service'dan oladi.

---

## Afzalliklari

1. **Modullik**:
   - Har bir mikroxizmat o'z sohasiga javobgar, bu esa ishlab chiqish va qo'llab-quvvatlashni osonlashtiradi.

2. **Masshtablilik**:
   - Alohida mikroxizmatlarni yuklamaga qarab masshtablash mumkin.

3. **Ma'lumotlarning izolyatsiyasi**:
   - Har bir mikroxizmat o'z ma'lumotlar bazasiga ega, bu xavfsizlik va mustaqillikni oshiradi.

4. **Moslashuvchanlik**:
   - Yangi mikroxizmatlarni qo'shish yoki mavjudlarini o'zgartirish oson.

---
