from fastapi import Request
from typing import Dict

# Dictionary containing translations for supported languages.
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
        "otp_verification_failed": "OTP verification failed",
        "comment_created": "Comment created successfully",
        "comment_updated": "Comment updated successfully",
        "comment_deleted": "Comment deleted successfully",
        "comment_not_found": "Comment not found",
        "payment_not_found": "Payment not found",
        "payment_already_exists": "Payment for this tariff already exists and is active",
        "payment_confirmed": "Payment confirmed and tokens added",
        "payment_failed": "Payment failed",
        "invalid_callback_data": "Invalid callback data",
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
        "otp_verification_failed": "Ошибка подтверждения OTP",
        "comment_created": "Комментарий успешно создан",
        "comment_updated": "Комментарий успешно обновлён",
        "comment_deleted": "Комментарий успешно удалён",
        "comment_not_found": "Комментарий не найден",
        "payment_not_found": "Платеж не найден",
        "payment_already_exists": "Платеж за этот тариф уже существует и активен",
        "payment_confirmed": "Платеж подтвержден и токены добавлены",
        "payment_failed": "Платеж не прошел",
        "invalid_callback_data": "Неверные данные обратного вызова",
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
        "otp_verification_failed": "OTPni tasdiqlashda xato",
        "comment_created": "Izoh muvaffaqiyatli yaratildi",
        "comment_updated": "Izoh muvaffaqiyatli yangilandi",
        "comment_deleted": "Izoh muvaffaqiyatli o'chirildi",
        "comment_not_found": "Izoh topilmadi",
        "payment_not_found": "To'lov topilmadi",
        "payment_already_exists": "Bu tarif uchun to'lov allaqachon mavjud va faol",
        "payment_confirmed": "To'lov tasdiqlandi va tokenlar qo'shildi",
        "payment_failed": "To'lov amalga oshmadi",
        "invalid_callback_data": "Noto'g'ri qayta chaqirish ma'lumotlari",
    },
}

def get_translation(request: Request) -> Dict[str, str]:
    """
    Dependency that returns the dictionary of translations for the requested language.
    Defaults to English if the language is not supported.
    """
    lang = request.headers.get("Accept-Language", "en").split(",")[0]
    return _TRANSLATIONS.get(lang, _TRANSLATIONS["en"])
