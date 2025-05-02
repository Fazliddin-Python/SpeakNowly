# Old URLs:
# Authentication and Authorization Endpoints
POST /accounts/login/                         # Login with email and password (body: {email, password})
POST /accounts/register-with-otp/             # Register with OTP (body: {email, password})
POST /accounts/check-register-otp/            # Verify OTP for registration (body: {email, code})
POST /accounts/resend-otp/                    # Resend OTP (body: {email, type})
POST /accounts/token/                         # Refresh JWT token (body: {refresh})
POST /accounts/login/oauth2                   # OAuth2 login (body: {token, auth_type})
PUT  /accounts/password-update/               # Update password (body: {old_password, new_password})
POST /accounts/forget-password/               # Request password reset (body: {email})
POST /accounts/check-forget-password-otp/     # Verify OTP for password reset (body: {email, code})
POST /accounts/set-new-password/              # Set new password (body: {password})
GET  /accounts/profile/                       # Get current user profile (no params)
PUT  /accounts/profile/update/                # Update current user profile (body: {first_name, last_name, age})
GET  /accounts/get-profile/{id}/              # Get user profile by ID (path: {id})

# Comments Endpoints
GET  /comments/                               # Get list of comments (no params)
POST /comments/                               # Create a comment (body: {text, rate})

# Notifications Endpoints
GET /notifications/messages/                  # Get notifications (query: {page, page_size})
GET /notifications/messages/{id}/             # Get notification by ID (path: {id})

# Payments Endpoints
POST /payments/checkout/                      # Create a payment (body: {user, tariff})
POST /payments/receive-payment-info/          # Get payment info (body: {user, tariff})

# Tariffs Endpoints
GET /tariffs/tariffs/                         # Get list of tariffs (no params)
GET /tariffs/tariffs/{id}/                    # Get tariff by ID (path: {id})

# Tests Endpoints
GET  /tests/history/                          # Get test history (no params)
GET  /tests/listening/analyse/{session_id}/   # Analyse listening test (path: {session_id})
GET  /tests/listening/part/{part_id}/         # Get listening test part (path: {part_id})
POST /tests/listening/start/                  # Start listening test (no params)
GET  /tests/listening/{id}/                   # Get listening test by ID (path: {id})
POST /tests/listening/{id}/cancel/            # Cancel listening test (path: {id})
POST /tests/listening/{session_id}/submit-answers/ # Submit listening answers (body: {answers}, path: {session_id})
GET  /tests/main/stats/                       # Get test statistics (no params)
GET  /tests/my-progress/                      # Get user progress (no params)
GET  /tests/reading/analysis/                 # Analyse reading test (no params)
POST /tests/reading/cancel/                   # Cancel reading test (no params)
POST /tests/reading/finish/                   # Finish reading test (body: {reading_id})
POST /tests/reading/open/                     # Open reading test (no params)
POST /tests/reading/passage/submit/           # Submit reading passage answers (body: {reading_id, passage_id, answers})
GET  /tests/reading/passage/{id}/             # Get reading passage by ID (path: {id})
POST /tests/reading/restart/                  # Restart reading test (no params)
POST /tests/reading/start/                    # Start reading test (body: {reading_id})
POST /tests/speaking/                         # Create speaking test (body: {start_time, end_time, status})
GET  /tests/speaking/{id}/                    # Get speaking test by ID (path: {id})
POST /tests/speaking/{id}/check/              # Check speaking test (formData: {part1_audio, part2_audio, part3_audio, is_finished, is_cancelled}, path: {id})
GET  /tests/top/                              # Get top tests (no params)
GET  /tests/top3/                             # Get top 3 tests (no params)
GET  /tests/user-responses/{session_id}/      # Get user responses (path: {session_id})
POST /tests/writing/                          # Create writing test (body: {status, start_time, end_time})
GET  /tests/writing/{id}/                     # Get writing test by ID (path: {id})
POST /tests/writing/{id}/check/               # Check writing test (body: {part1, part2, is_finished, is_cancelled}, path: {id})


# New URLs:
# Authentication and Authorization Endpoints
POST   /api/v1/auth/login/                     # User login (body: {email, password})
POST   /api/v1/auth/register/otp/             # Register with OTP (body: {email, password})
POST   /api/v1/auth/register/otp/verify/      # Verify OTP for registration (body: {email, code})
POST   /api/v1/auth/otp/resend/               # Resend OTP (body: {email, type})
POST   /api/v1/auth/token/refresh/            # Refresh JWT token (body: {refresh})
POST   /api/v1/auth/oauth2/                   # OAuth2 login (body: {token, auth_type})
PUT    /api/v1/auth/password/update/          # Update password (body: {old_password, new_password})
POST   /api/v1/auth/password/forget/          # Request password reset (body: {email})
POST   /api/v1/auth/password/forget/verify/   # Verify OTP for password reset (body: {email, code})
POST   /api/v1/auth/password/reset/           # Set new password (body: {password})
GET    /api/v1/users/me/                      # Get current user profile (no params)
PUT    /api/v1/users/me/update/               # Update current user profile (body: {first_name, last_name, age})
GET    /api/v1/users/{id}/                    # Get user profile by ID (path: {id})

# Comments Endpoints
GET    /api/v1/comments/                      # Get list of comments (query: {page, page_size})
POST   /api/v1/comments/                      # Create a new comment (body: {text, rate})

# Notifications Endpoints
GET    /api/v1/notifications/                 # Get list of notifications (query: {page, page_size})
GET    /api/v1/notifications/{id}/            # Get notification by ID (path: {id})

# Payments Endpoints
POST   /api/v1/payments/checkout/             # Create a payment (body: {user_id, tariff_id})
POST   /api/v1/payments/info/                 # Get payment info (body: {user_id, tariff_id})

# Tariffs Endpoints
GET    /api/v1/tariffs/                       # Get list of tariffs (query: {is_active, category})
GET    /api/v1/tariffs/{id}/                  # Get tariff by ID (path: {id})

# Tests Endpoints
GET    /api/v1/tests/history/                 # Get test history (query: {user_id, test_type})
GET    /api/v1/tests/listening/{session_id}/analyse/ # Analyse listening test (path: {session_id})
GET    /api/v1/tests/listening/part/{part_id}/# Get listening test part (path: {part_id})
POST   /api/v1/tests/listening/start/         # Start listening test (body: {user_id, test_id})
GET    /api/v1/tests/listening/{id}/          # Get listening test by ID (path: {id})
POST   /api/v1/tests/listening/{id}/cancel/   # Cancel listening test (path: {id})
POST   /api/v1/tests/listening/{session_id}/submit/ # Submit listening test answers (body: {answers}, path: {session_id})
GET    /api/v1/tests/stats/                   # Get test statistics (query: {user_id})
GET    /api/v1/tests/progress/                # Get user progress (query: {user_id})
GET    /api/v1/tests/reading/analysis/        # Analyse reading test (query: {user_id})
POST   /api/v1/tests/reading/cancel/          # Cancel reading test (body: {test_id})
POST   /api/v1/tests/reading/finish/          # Finish reading test (body: {test_id})
POST   /api/v1/tests/reading/open/            # Open reading test (body: {test_id})
POST   /api/v1/tests/reading/passage/submit/  # Submit reading passage answers (body: {test_id, passage_id, answers})
GET    /api/v1/tests/reading/passage/{id}/    # Get reading passage by ID (path: {id})
POST   /api/v1/tests/reading/restart/         # Restart reading test (body: {test_id})
POST   /api/v1/tests/reading/start/           # Start reading test (body: {test_id})
POST   /api/v1/tests/speaking/                # Create speaking test (body: {user_id, start_time, end_time, status})
GET    /api/v1/tests/speaking/{id}/           # Get speaking test by ID (path: {id})
POST   /api/v1/tests/speaking/{id}/check/     # Check speaking test (formData: {part1_audio, part2_audio, part3_audio, is_finished, is_cancelled}, path: {id})
GET    /api/v1/tests/top/                     # Get top tests (query: {limit})
GET    /api/v1/tests/top3/                    # Get top 3 tests (no params)
GET    /api/v1/tests/user-responses/{session_id}/ # Get user responses (path: {session_id})
POST   /api/v1/tests/writing/                 # Create writing test (body: {user_id, status, start_time, end_time})
GET    /api/v1/tests/writing/{id}/            # Get writing test by ID (path: {id})
POST   /api/v1/tests/writing/{id}/check/      # Check writing test (body: {part1, part2, is_finished, is_cancelled}, path: {id})