from fastapi import Request, Depends
from typing import Dict

_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "user_already_registered": "This email is already registered",
        "verification_sent": "Verification code has been sent",
        "verification_resent": "Verification code has been resent",
        "user_not_found": "User not found",
        "incorrect_password": "Incorrect password",
        "profile_updated": "Profile updated successfully",
        "password_updated": "Password updated successfully",
        "code_confirmed": "Code confirmed",
        "code_resent": "Verification code resent",
        "email_not_verified": "Email not verified",
        "too_many_attempts": "Too many attempts, please try again later",
        "otp_resend_failed": "Failed to resend OTP, please try again",
        "inactive_user": "User is inactive",
        "email_not_verified": "Email not verified",
        "otp_verification_failed": "OTP verification failed",
    },
    "ru": {
        "user_already_registered": "Этот email уже зарегистрирован",
        "verification_sent": "Код подтверждения отправлен",
        "verification_resent": "Код подтверждения отправлен повторно",
        "user_not_found": "Пользователь не найден",
        "incorrect_password": "Неверный пароль",
        "profile_updated": "Профиль успешно обновлён",
        "password_updated": "Пароль успешно обновлён",
        "code_confirmed": "Код подтверждён",
        "code_resent": "Код подтверждения отправлен повторно",
        "email_not_verified": "Email не подтверждён",
        "too_many_attempts": "Слишком много попыток, попробуйте позже",
        "otp_resend_failed": "Не удалось повторно отправить OTP, попробуйте снова",
        "inactive_user": "Пользователь неактивен",
        "email_not_verified": "Email не подтверждён",
        "otp_verification_failed": "Ошибка подтверждения OTP",
    },
    "uz": {
        "user_already_registered": "Bu email allaqachon ro'yxatdan o'tgan",
        "verification_sent": "Tasdiqlash kodi yuborildi",
        "verification_resent": "Tasdiqlash kodi qayta yuborildi",
        "user_not_found": "Foydalanuvchi topilmadi",
        "incorrect_password": "Parol noto'g'ri",
        "profile_updated": "Profil muvaffaqiyatli yangilandi",
        "password_updated": "Parol muvaffaqiyatli yangilandi",
        "code_confirmed": "Kod tasdiqlandi",
        "code_resent": "Tasdiqlash kodi yuborildi",
        "email_not_verified": "Email tasdiqlanmagan",
        "too_many_attempts": "Juda ko'p urinishlar, iltimos keyinroq urinib ko'ring",
        "otp_resend_failed": "OTPni qayta yuborishda xato, iltimos qayta urinib ko'ring",
        "inactive_user": "Foydalanuvchi faol emas",
        "email_not_verified": "Email tasdiqlanmagan",
        "otp_verification_failed": "OTPni tasdiqlashda xato",
    },
}

def get_translation(request: Request) -> Dict[str, str]:
    """
    Dependency: returns the dict of translations for requested language.
    """
    lang = request.headers.get("Accept-Language", "en").split(",")[0]
    return _TRANSLATIONS.get(lang, _TRANSLATIONS["en"])
