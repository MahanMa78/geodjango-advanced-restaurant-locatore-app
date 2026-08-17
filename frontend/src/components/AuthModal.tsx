import React, { useState } from 'react';
import { sendOtpApi, verifyOtpApi } from '../api';
import type { User } from '../types';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [step, setStep] = useState<'PHONE' | 'CODE'>('PHONE');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [code, setCode] = useState('');
  const [devCode, setDevCode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phoneNumber.startsWith('09') || phoneNumber.length !== 11) {
      setError('لطفاً یک شماره موبایل معتبر ۱۱ رقمی (مثلاً ۰۹۱۲۳۴۵۶۷۸۹) وارد کنید.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await sendOtpApi(phoneNumber);
      if (res.dev_code) {
        setDevCode(res.dev_code);
      }
      setStep('CODE');
    } catch (err: any) {
      setError(err.response?.data?.error || 'خطا در ارسال کد تایید. لطفاً دوباره تلاش کنید.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (code.length < 4) {
      setError('لطفاً کد تایید دریافتی را وارد کنید.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await verifyOtpApi(phoneNumber, code);
      
      // ذخیره توکن‌ها در حافظه محلی
      localStorage.setItem('access_token', res.tokens.access);
      localStorage.setItem('refresh_token', res.tokens.refresh);
      
      onSuccess(res.user);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.error || 'کد تایید نامعتبر است یا منقضی شده است.');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToPhone = () => {
    setStep('PHONE');
    setCode('');
    setDevCode(null);
    setError(null);
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.65)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000,
      direction: 'rtl'
    }}>
      <div style={{
        backgroundColor: '#fff',
        borderRadius: '12px',
        padding: '24px',
        width: '100%',
        maxWidth: '380px',
        boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
        position: 'relative'
      }}>
        {/* دکمه بستن */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            background: 'none',
            border: 'none',
            fontSize: '18px',
            cursor: 'pointer',
            color: '#666'
          }}
        >
          ✕
        </button>

        <h3 style={{ margin: '0 0 16px', textAlign: 'center', color: '#1a1a1a' }}>
          {step === 'PHONE' ? 'ورود یا ثبت‌نام' : 'تایید کد پیامک‌شده'}
        </h3>

        {error && (
          <div style={{
            backgroundColor: '#ffebee',
            color: '#c62828',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '13px',
            marginBottom: '12px',
            textAlign: 'center'
          }}>
            {error}
          </div>
        )}

        {devCode && step === 'CODE' && (
          <div style={{
            backgroundColor: '#e8f5e9',
            color: '#2e7d32',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '13px',
            marginBottom: '12px',
            textAlign: 'center'
          }}>
            کد تایید تستی: <strong>{devCode}</strong>
          </div>
        )}

        {step === 'PHONE' ? (
          <form onSubmit={handleSendOtp}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', color: '#444' }}>
                شماره موبایل
              </label>
              <input
                type="tel"
                placeholder="۰۹۱۲۳۴۵۶۷۸۹"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #ccc',
                  fontSize: '15px',
                  boxSizing: 'border-box',
                  textAlign: 'left',
                  direction: 'ltr'
                }}
                disabled={loading}
                autoFocus
              />
            </div>
            <button
              type="submit"
              disabled={loading || !phoneNumber}
              style={{
                width: '100%',
                padding: '10px',
                backgroundColor: '#e53935',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                fontSize: '15px',
                fontWeight: 'bold',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading || !phoneNumber ? 0.7 : 1
              }}
            >
              {loading ? 'در حال ارسال...' : 'دریافت کد تایید'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp}>
            <p style={{ fontSize: '13px', color: '#666', marginBottom: '12px', textAlign: 'center' }}>
              کد ارسال‌شده به شماره {phoneNumber} را وارد کنید.
            </p>
            <div style={{ marginBottom: '16px' }}>
              <input
                type="text"
                placeholder="کد ۵ رقمی"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #ccc',
                  fontSize: '18px',
                  boxSizing: 'border-box',
                  textAlign: 'center',
                  letterSpacing: '4px'
                }}
                disabled={loading}
                autoFocus
              />
            </div>
            <button
              type="submit"
              disabled={loading || !code}
              style={{
                width: '100%',
                padding: '10px',
                backgroundColor: '#2e7d32',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                fontSize: '15px',
                fontWeight: 'bold',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading || !code ? 0.7 : 1,
                marginBottom: '8px'
              }}
            >
              {loading ? 'در حال بررسی...' : 'ورود به حساب'}
            </button>
            <button
              type="button"
              onClick={handleBackToPhone}
              style={{
                width: '100%',
                background: 'none',
                border: 'none',
                color: '#666',
                fontSize: '13px',
                cursor: 'pointer',
                padding: '4px'
              }}
            >
              ویرایش شماره موبایل
            </button>
          </form>
        )}
      </div>
    </div>
  );
};