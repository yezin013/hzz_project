import React from 'react';
import styles from './LoadingSpinner.module.css';

interface LoadingSpinnerProps {
    message?: string;
    theme?: 'food' | 'cocktail' | 'hansang';
}

export default function LoadingSpinner({
    message = "한상차림 준비 중",
    theme = 'hansang'
}: LoadingSpinnerProps) {
    const getThemeEmoji = () => {
        switch (theme) {
            case 'food':
                return ['🍽️', '🍱', '🥘', '🍚'];
            case 'cocktail':
                return ['🍹', '🍸', '🥃', '🍷'];
            case 'hansang':
            default:
                return ['🍚', '🥣', '🥢', '🍵'];
        }
    };

    const emojis = getThemeEmoji().slice(0, 3); // 3개만 사용

    return (
        <div className={styles.container}>
            <div className={styles.emojiRow}>
                {emojis.map((emoji, index) => (
                    <div
                        key={index}
                        className={styles.emoji}
                        style={{
                            animationDelay: `${index * 0.2}s`
                        }}
                    >
                        {emoji}
                    </div>
                ))}
            </div>
            <h4 className={styles.message}>{message}</h4>
            <p className={styles.subMessage}>잠시만 기다려주세요...</p>
        </div>
    );
}
