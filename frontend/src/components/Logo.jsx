import React from 'react';

export const Logo = ({ className }) => {
    return (
        <a 
            href="/" 
            style={{
                display: 'flex', 
                alignItems: 'center', 
                gap: '10px', 
                textDecoration: 'none'
            }}
            className={className}
        >
            {/* Icon */}
            <svg width="52" height="52" viewBox="0 0 82 82" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="ig" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#3B82F6"/>
                        <stop offset="100%" stopColor="#1D4ED8"/>
                    </linearGradient>
                </defs>
                <rect width="82" height="82" rx="16" fill="url(#ig)"/>
                <polygon points="41,10 71,21 41,32 11,21" fill="#fff"/>
                <rect x="35" y="21" width="12" height="14" rx="2" fill="#fff" opacity="0.9"/>
                <line x1="71" y1="21" x2="71" y2="38" stroke="#fff" strokeWidth="2.5" strokeLinecap="round"/>
                <circle cx="71" cy="41" r="3.5" fill="#FCD34D"/>
                <rect x="10" y="58" width="62" height="15" rx="7.5" fill="#0f172a"/>
                <text x="41" y="70" textAnchor="middle"
                    fontFamily="'Segoe UI',Arial,sans-serif"
                    fontSize="9" fontWeight="800" fill="#fff" letterSpacing="3">LMS</text>
            </svg>

            {/* Wordmark */}
            <span style={{
                fontFamily: "'Segoe UI',Arial,sans-serif", 
                fontSize: '26px', 
                fontWeight: '800', 
                letterSpacing: '-0.5px', 
                lineHeight: '1'
            }}>
                <span style={{ color: '#0f172a' }}>Class</span>
                <span style={{ color: '#2563EB' }}>ora</span>
            </span>
        </a>
    );
};

export default Logo;
