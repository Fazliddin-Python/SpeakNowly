from fastapi import Request
from typing import Dict

_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # --- User/Auth ---
        "user_already_registered": "This email is already registered",
        "user_not_found": "User not found",
        "inactive_user": "User is inactive",
        "invalid_credentials": "Invalid email or password",
        "email_not_verified": "Email not verified",
        "too_many_attempts": "Too many attempts, please try again later",
        "internal_error": "Internal server error",
        "invalid_oauth2_token": "Invalid OAuth2 token",
        "email_already_in_use": "This email is already in use",
        "password_too_weak": "Password is too weak",
        "invalid_email_format": "Invalid email format",

        # --- Verification/OTP ---
        "verification_sent": "Verification code has been sent",
        "verification_resent": "Verification code has been resent",
        "otp_resend_failed": "Failed to resend OTP, please try again",
        "otp_verification_failed": "OTP verification failed",
        "code_confirmed": "Code confirmed",
        "code_resent": "Verification code resent",

        # --- Profile/Password ---
        "profile_updated": "Profile updated successfully",
        "password_updated": "Password updated successfully",
        "incorrect_password": "Incorrect password",

        # --- Comments ---
        "comment_created": "Comment created successfully",
        "comment_updated": "Comment updated successfully",
        "comment_deleted": "Comment deleted successfully",
        "comment_not_found": "Comment not found",

        # --- Payments ---
        "payment_not_found": "Payment not found",
        "payment_already_exists": "Payment for this tariff already exists and is active",
        "payment_confirmed": "Payment confirmed and tokens added",
        "payment_failed": "Payment failed",

        # --- Other ---
        "invalid_callback_data": "Invalid callback data",
        "question_not_found": "Question not found",
        "listening_session_not_found": "Listening session not found",
        "no_listening_tests": "No listening tests available",
        "session_already_completed": "Session already completed",
        "listening_test_not_found": "Listening test not found",
        "answers_submitted": "Answers submitted successfully",
        "session_cancelled": "Session cancelled successfully",
        "no_reading_tests": "No reading tests available",
        "reading_not_found": "Reading test not found",
        "no_passages": "No passages available for reading test",
        "reading_already_completed": "Reading test already completed",
    },
    "ru": {
        # --- User/Auth ---
        "user_already_registered": "Этот email уже зарегистрирован",
        "user_not_found": "Пользователь не найден",
        "inactive_user": "Пользователь неактивен",
        "invalid_credentials": "Неверный логин или пароль",
        "email_not_verified": "Email не подтверждён",
        "too_many_attempts": "Слишком много попыток, попробуйте позже",
        "internal_error": "Внутренняя ошибка сервера",
        "invalid_oauth2_token": "Неверный OAuth2 токен",
        "email_already_in_use": "Этот email уже используется",
        "password_too_weak": "Пароль слишком простой",
        "invalid_email_format": "Некорректный формат email",

        # --- Verification/OTP ---
        "verification_sent": "Код подтверждения отправлен",
        "verification_resent": "Код подтверждения отправлен повторно",
        "otp_resend_failed": "Не удалось повторно отправить OTP, попробуйте снова",
        "otp_verification_failed": "Ошибка подтверждения OTP",
        "code_confirmed": "Код подтверждён",
        "code_resent": "Код подтверждения отправлен повторно",

        # --- Profile/Password ---
        "profile_updated": "Профиль успешно обновлён",
        "password_updated": "Пароль успешно обновлён",
        "incorrect_password": "Неверный пароль",

        # --- Comments ---
        "comment_created": "Комментарий успешно создан",
        "comment_updated": "Комментарий успешно обновлён",
        "comment_deleted": "Комментарий успешно удалён",
        "comment_not_found": "Комментарий не найден",

        # --- Payments ---
        "payment_not_found": "Платеж не найден",
        "payment_already_exists": "Платеж за этот тариф уже существует и активен",
        "payment_confirmed": "Платеж подтвержден и токены добавлены",
        "payment_failed": "Платеж не прошел",

        # --- Other ---
        "invalid_callback_data": "Неверные данные обратного вызова",
        "question_not_found": "Вопрос не найден",
        "listening_session_not_found": "Сессия прослушивания не найдена",
        "no_listening_tests": "Нет доступных тестов прослушивания",
        "session_already_completed": "Сессия уже завершена",
        "listening_test_not_found": "Тест прослушивания не найден",
        "answers_submitted": "Ответы успешно отправлены",
    },
    "uz": {
        # --- User/Auth ---
        "user_already_registered": "Bu email allaqachon ro'yxatdan o'tgan",
        "user_not_found": "Foydalanuvchi topilmadi",
        "inactive_user": "Foydalanuvchi faol emas",
        "invalid_credentials": "Login yoki parol noto‘g‘ri",
        "email_not_verified": "Email tasdiqlanmagan",
        "too_many_attempts": "Juda ko'p urinishlar, iltimos keyinroq urinib ko'ring",
        "internal_error": "Ichki server xatosi",
        "invalid_oauth2_token": "Noto'g'ri OAuth2 token",
        "email_already_in_use": "Bu email allaqachon ishlatilmoqda",
        "password_too_weak": "Parol juda oddiy",
        "invalid_email_format": "Email formati noto'g'ri",

        # --- Verification/OTP ---
        "verification_sent": "Tasdiqlash kodi yuborildi",
        "verification_resent": "Tasdiqlash kodi qayta yuborildi",
        "otp_resend_failed": "OTPni qayta yuborishda xato, iltimos qayta urinib ko'ring",
        "otp_verification_failed": "OTPni tasdiqlashda xato",
        "code_confirmed": "Kod tasdiqlandi",
        "code_resent": "Tasdiqlash kodi yuborildi",

        # --- Profile/Password ---
        "profile_updated": "Profil muvaffaqiyatli yangilandi",
        "password_updated": "Parol muvaffaqiyatli yangilandi",
        "incorrect_password": "Parol noto'g'ri",

        # --- Comments ---
        "comment_created": "Izoh muvaffaqiyatli yaratildi",
        "comment_updated": "Izoh muvaffaqiyatli yangilandi",
        "comment_deleted": "Izoh muvaffaqiyatli o'chirildi",
        "comment_not_found": "Izoh topilmadi",

        # --- Payments ---
        "payment_not_found": "To'lov topilmadi",
        "payment_already_exists": "Bu tarif uchun to'lov allaqachon mavjud va faol",
        "payment_confirmed": "To'lov tasdiqlandi va tokenlar qo'shildi",
        "payment_failed": "To'lov amalga oshmadi",

        # --- Other ---
        "invalid_callback_data": "Noto'g'ri qayta chaqirish ma'lumotlari",
        "question_not_found": "Savol topilmadi",
        "listening_session_not_found": "Tinglash sessiyasi topilmadi",
        "no_listening_tests": "Tinglash testlari mavjud emas",
        "session_already_completed": "Sessiya allaqachon yakunlangan",
        "listening_test_not_found": "Tinglash testi topilmadi",
        "answers_submitted": "Javoblar muvaffaqiyatli yuborildi",
    },
}

def get_translation(request: Request) -> Dict[str, str]:
    """
    Dependency that returns the dictionary of translations for the requested language.
    Defaults to English if the language is not supported.
    """
    lang = request.headers.get("Accept-Language", "en").split(",")[0]
    return _TRANSLATIONS.get(lang, _TRANSLATIONS["en"])
