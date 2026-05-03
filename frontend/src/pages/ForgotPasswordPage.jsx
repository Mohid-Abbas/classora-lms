import { useState, useRef, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { forgotPasswordRequest, resetPasswordRequest } from "../api/auth";
import { Logo } from "../components/Logo";
import "./LoginPage.css";
import "./ForgotPasswordPage.css";

export default function ForgotPasswordPage() {
  const navigate = useNavigate();

  // step: 1 = email entry, 2 = code entry, 3 = new password, 4 = success
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState(["", "", "", "", "", ""]);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [resendTimer, setResendTimer] = useState(0);

  const codeRefs = useRef([]);

  // Resend cooldown timer
  useEffect(() => {
    if (resendTimer <= 0) return;
    const interval = setInterval(() => {
      setResendTimer((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [resendTimer]);

  // Auto-focus first code input when entering step 2
  useEffect(() => {
    if (step === 2 && codeRefs.current[0]) {
      codeRefs.current[0].focus();
    }
  }, [step]);

  /* -------- Step 1: Send verification code -------- */
  const handleSendCode = async (e) => {
    e.preventDefault();
    setError("");

    if (!email) {
      setError("Email address is required.");
      return;
    }

    try {
      setSubmitting(true);
      await forgotPasswordRequest(email);
      setStep(2);
      setResendTimer(60);
    } catch (err) {
      if (err.response) {
        const { data } = err.response;
        setError(typeof data === "string" ? data : (data.detail || "Failed to send reset email"));
      } else {
        setError("Connection failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  /* -------- Step 2: Verify OTP code -------- */
  const handleCodeChange = (index, value) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);

    // Auto-advance to next input
    if (value && index < 5) {
      codeRefs.current[index + 1]?.focus();
    }
  };

  const handleCodeKeyDown = (index, e) => {
    if (e.key === "Backspace" && !code[index] && index > 0) {
      codeRefs.current[index - 1]?.focus();
    }
  };

  const handleCodePaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (!pasted) return;
    const newCode = [...code];
    for (let i = 0; i < 6; i++) {
      newCode[i] = pasted[i] || "";
    }
    setCode(newCode);
    // Focus the next empty or last input
    const nextEmpty = newCode.findIndex((c) => !c);
    codeRefs.current[nextEmpty === -1 ? 5 : nextEmpty]?.focus();
  };

  const handleVerifyCode = (e) => {
    e.preventDefault();
    setError("");
    const fullCode = code.join("");
    if (fullCode.length !== 6) {
      setError("Please enter the complete 6-digit code.");
      return;
    }
    setStep(3);
  };

  const handleResendCode = async () => {
    if (resendTimer > 0) return;
    setError("");
    try {
      setSubmitting(true);
      await forgotPasswordRequest(email);
      setCode(["", "", "", "", "", ""]);
      setResendTimer(60);
    } catch {
      setError("Failed to resend code. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  /* -------- Step 3: Reset password -------- */
  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError("");

    if (!newPassword) {
      setError("New password is required.");
      return;
    }
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setSubmitting(true);
      const fullCode = code.join("");
      await resetPasswordRequest(email, fullCode, newPassword);
      setStep(4);
    } catch (err) {
      if (err.response) {
        const { data } = err.response;
        setError(typeof data === "string" ? data : (data.detail || "Failed to reset password."));
      } else {
        setError("Connection failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  /* -------- Step indicator dots -------- */
  const StepIndicator = () => (
    <div className="fp-step-indicator">
      {[1, 2, 3].map((s) => (
        <div
          key={s}
          className={`fp-step-dot ${step >= s ? "fp-step-dot--active" : ""} ${step === s ? "fp-step-dot--current" : ""}`}
        />
      ))}
    </div>
  );

  /* ================ STEP 4: SUCCESS ================ */
  if (step === 4) {
    return (
      <div className="login-page-container">
        <div className="login-content">
          <div className="login-logo-wrapper">
            <Link to="/"><Logo className="login-logo-svg" /></Link>
          </div>
          <div className="login-slogan">Empowering Education Together</div>
          <div className="login-form-card">
            <div className="fp-success-block">
              <div className="fp-success-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="white">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                </svg>
              </div>
              <h3 className="fp-heading">Password Reset!</h3>
              <p className="fp-subtext">
                Your password has been updated successfully. You can now sign in with your new password.
              </p>
            </div>
            <button
              type="button"
              className="pill-submit-btn"
              onClick={() => navigate("/login")}
              style={{ marginTop: "20px" }}
            >
              Sign In
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* ================ STEPS 1-3 ================ */
  return (
    <div className="login-page-container">
      <div className="login-content">
        <div className="login-logo-wrapper">
          <Link to="/"><Logo className="login-logo-svg" /></Link>
        </div>
        <div className="login-slogan">Empowering Education Together</div>

        <div className="login-form-card">
          <StepIndicator />

          {/* -------- STEP 1: Enter email -------- */}
          {step === 1 && (
            <>
              <h2 className="fp-heading">Forgot Password</h2>
              <p className="fp-subtext">
                Enter your email address and we&apos;ll send you a verification code.
              </p>

              {error && <div className="pill-error-msg">{error}</div>}

              <form onSubmit={handleSendCode}>
                <div className="pill-input-wrapper">
                  <div className="pill-input-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
                    </svg>
                  </div>
                  <div className="pill-input-divider"></div>
                  <input
                    id="fp-email-input"
                    className="pill-input-field"
                    type="email"
                    placeholder="EMAIL ADDRESS"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                    required
                  />
                </div>

                <button
                  id="fp-send-code-btn"
                  type="submit"
                  className="pill-submit-btn"
                  disabled={submitting}
                  style={{ marginTop: "20px" }}
                >
                  {submitting ? "Sending..." : "Send Verification Code"}
                </button>
              </form>
            </>
          )}

          {/* -------- STEP 2: Enter OTP code -------- */}
          {step === 2 && (
            <>
              <div className="fp-email-badge">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
                </svg>
                <span>{email}</span>
              </div>
              <h2 className="fp-heading">Enter Verification Code</h2>
              <p className="fp-subtext">
                We&apos;ve sent a 6-digit code to your email. Enter it below.
              </p>

              {error && <div className="pill-error-msg">{error}</div>}

              <form onSubmit={handleVerifyCode}>
                <div className="fp-code-inputs" onPaste={handleCodePaste}>
                  {code.map((digit, i) => (
                    <input
                      key={i}
                      id={`fp-code-input-${i}`}
                      ref={(el) => (codeRefs.current[i] = el)}
                      className={`fp-code-box ${digit ? "fp-code-box--filled" : ""}`}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleCodeChange(i, e.target.value)}
                      onKeyDown={(e) => handleCodeKeyDown(i, e)}
                      autoComplete="one-time-code"
                    />
                  ))}
                </div>

                <button
                  id="fp-verify-code-btn"
                  type="submit"
                  className="pill-submit-btn"
                  disabled={submitting}
                  style={{ marginTop: "24px" }}
                >
                  Verify Code
                </button>
              </form>

              <div className="fp-resend-row">
                <span className="fp-resend-text">Didn&apos;t receive the code?</span>
                <button
                  id="fp-resend-btn"
                  type="button"
                  className="fp-resend-btn"
                  onClick={handleResendCode}
                  disabled={resendTimer > 0 || submitting}
                >
                  {resendTimer > 0 ? `Resend in ${resendTimer}s` : "Resend Code"}
                </button>
              </div>

              <button
                type="button"
                className="fp-back-link"
                onClick={() => { setStep(1); setError(""); setCode(["", "", "", "", "", ""]); }}
              >
                ← Change email
              </button>
            </>
          )}

          {/* -------- STEP 3: New password -------- */}
          {step === 3 && (
            <>
              <h2 className="fp-heading">Create New Password</h2>
              <p className="fp-subtext">
                Your code has been verified. Enter your new password below.
              </p>

              {error && <div className="pill-error-msg">{error}</div>}

              <form onSubmit={handleResetPassword}>
                <div className="pill-input-wrapper">
                  <div className="pill-input-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1s3.1 1.39 3.1 3.1v2z" />
                    </svg>
                  </div>
                  <div className="pill-input-divider"></div>
                  <input
                    id="fp-new-password-input"
                    className="pill-input-field"
                    type={showPassword ? "text" : "password"}
                    placeholder="NEW PASSWORD"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    autoComplete="new-password"
                    required
                  />
                  <button
                    type="button"
                    className="fp-eye-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? (
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="#a0aec0">
                        <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z" />
                      </svg>
                    ) : (
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="#a0aec0">
                        <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
                      </svg>
                    )}
                  </button>
                </div>

                <div className="pill-input-wrapper">
                  <div className="pill-input-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1s3.1 1.39 3.1 3.1v2z" />
                    </svg>
                  </div>
                  <div className="pill-input-divider"></div>
                  <input
                    id="fp-confirm-password-input"
                    className="pill-input-field"
                    type={showPassword ? "text" : "password"}
                    placeholder="CONFIRM PASSWORD"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    autoComplete="new-password"
                    required
                  />
                </div>

                <button
                  id="fp-reset-password-btn"
                  type="submit"
                  className="pill-submit-btn"
                  disabled={submitting}
                  style={{ marginTop: "10px" }}
                >
                  {submitting ? "Resetting..." : "Reset Password"}
                </button>
              </form>

              <button
                type="button"
                className="fp-back-link"
                onClick={() => { setStep(2); setError(""); }}
              >
                ← Back to code entry
              </button>
            </>
          )}
        </div>

        <p className="pill-register-footer">
          Remember your password?
          <button type="button" onClick={() => navigate("/login")}>
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
