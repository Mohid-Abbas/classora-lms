import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { resetPasswordRequest } from "../api/auth";
import { Logo } from "../components/Logo";
import "./LoginPage.css";

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!email || !code || !newPassword || !confirmPassword) {
      setError("All fields are required.");
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
      await resetPasswordRequest(email, code, newPassword);
      setSuccess(true);
    } catch (err) {
      if (err.response) {
        const { data } = err.response;
        setError(typeof data === "string" ? data : (data.detail || "Failed to reset password"));
      } else {
        setError("Connection failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  

  if (success) {
    return (
      <div className="login-page-container">
        <div className="login-content">
          <div className="login-logo-wrapper">
            <Link to="/">
              <Logo className="login-logo-svg" />
            </Link>
          </div>

          <div className="login-slogan">
            Empowering Education Together
          </div>

          <div className="login-form-card">
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ 
                width: '60px', 
                height: '60px', 
                backgroundColor: '#10b981', 
                borderRadius: '50%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                margin: '0 auto 20px'
              }}>
                <svg width="30" height="30" viewBox="0 0 24 24" fill="white">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
              </div>
              <h3 style={{ color: '#0f172a', marginBottom: '15px' }}>Password Reset Successful</h3>
              <p style={{ color: '#64748b', lineHeight: '1.6' }}>
                Your password has been reset successfully.
              </p>
              <p style={{ color: '#64748b', lineHeight: '1.6' }}>
                You can now login with your new password.
              </p>
            </div>

            <button
              type="button"
              className="pill-submit-btn"
              onClick={() => navigate("/login")}
              style={{ marginTop: '20px' }}
            >
              Go to Login
            </button>
          </div>

          <p className="pill-register-footer">
            Don't have an account?
            <button type="button" onClick={() => navigate("/register")}>
              Register here
            </button>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page-container">
      <div className="login-content">
        <div className="login-logo-wrapper">
          <Link to="/">
            <Logo className="login-logo-svg" />
          </Link>
        </div>

        <div className="login-slogan">
          Empowering Education Together
        </div>

        <div className="login-form-card">
          <h2 style={{ textAlign: 'center', color: '#0f172a', marginBottom: '30px' }}>
            Reset Password (Enter Code)
          </h2>
          
          {error && <div className="pill-error-msg">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="pill-input-wrapper">
              <div className="pill-input-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
                </svg>
              </div>
              <div className="pill-input-divider"></div>
              <input
                className="pill-input-field"
                type="email"
                placeholder="EMAIL ADDRESS"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>

            <div className="pill-input-wrapper">
              <div className="pill-input-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
                </svg>
              </div>
              <div className="pill-input-divider"></div>
              <input
                className="pill-input-field"
                type="text"
                placeholder="VERIFICATION CODE"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
              />
            </div>

            <div className="pill-input-wrapper">
              <div className="pill-input-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" />
                </svg>
              </div>
              <div className="pill-input-divider"></div>
              <input
                className="pill-input-field"
                type="password"
                placeholder="NEW PASSWORD"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>

            <div className="pill-input-wrapper">
              <div className="pill-input-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" />
                </svg>
              </div>
              <div className="pill-input-divider"></div>
              <input
                className="pill-input-field"
                type="password"
                placeholder="CONFIRM NEW PASSWORD"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>

            <button
              type="submit"
              className="pill-submit-btn"
              disabled={submitting}
              style={{ marginTop: '20px' }}
            >
              {submitting ? "Resetting..." : "Reset Password"}
            </button>
          </form>
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
