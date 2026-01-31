"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { signIn, signOut, useSession } from "next-auth/react";
import { useState } from "react";
import { Menu, X, Search } from "lucide-react";
import RealTimeSearchRanking from "./RealTimeSearchRanking";
import styles from "./Header.module.css";

interface HeaderProps {
    cognitoDomain?: string;
    clientId?: string;
}

export default function Header({ cognitoDomain, clientId }: HeaderProps) {
    const { data: session } = useSession();
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
    const closeMenu = () => setIsMenuOpen(false);

    const handleSignOut = async () => {
        const logoutRedirectUri = window.location.origin;

        // Sign out from NextAuth first
        await signOut({ redirect: false });

        // Then redirect to Cognito logout to clear Cognito session
        if (cognitoDomain && clientId) {
            // Construct Cognito logout URL
            const logoutUrl = `${cognitoDomain}/logout?client_id=${clientId}&logout_uri=${encodeURIComponent(logoutRedirectUri)}`;
            window.location.href = logoutUrl;
        } else {
            // Fallback if env vars not set
            window.location.replace("/");
        }
    };

    const pathname = usePathname();

    const handleLogoClick = (e: React.MouseEvent) => {
        if (pathname === '/') {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    return (
        <header className={styles.header}>
            <Link href="/" className={styles.logoSection} onClick={handleLogoClick}>
                <Image
                    src="/logo.png"
                    alt="한잔酒 Logo"
                    width={80}
                    height={80}
                    style={{ objectFit: 'contain' }}
                />
                <span>한잔酒</span>
            </Link>

            <nav className={styles.nav}>
                <Link href="/ocr" className={styles.navLink}>
                    이미지로 찾기
                </Link>
                <Link href="/?view=list#body-section" className={styles.navLink}>
                    전통주 리스트
                </Link>
                <Link href="/map" className={styles.navLink}>
                    주막 지도
                </Link>
                <Link href="/board" className={styles.navLink}>
                    커뮤니티
                </Link>
                <Link href="/mypage" className={styles.navLink}>
                    마이페이지
                </Link>
            </nav>

            <div className={styles.authSection}>
                <Link href="/?view=list#body-section" className={styles.searchIconLink}>
                    <Search size={24} color="#3e2723" />
                </Link>
                <RealTimeSearchRanking />
                {session ? (
                    <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                        <span style={{ fontSize: "0.9rem", color: "#3e2723", fontWeight: "600" }}>{session.user?.name}님</span>
                        <button
                            className={styles.loginButton}
                            onClick={handleSignOut}
                        >
                            로그아웃
                        </button>
                    </div>
                ) : (
                    <button
                        className={styles.loginButton}
                        onClick={() => signIn("cognito", { callbackUrl: "/" })}
                    >
                        로그인
                    </button>
                )}
                <button className={styles.mobileMenuBtn} onClick={toggleMenu}>
                    <Menu size={24} color="#3e2723" />
                </button>
            </div>

            {/* Mobile Menu Overlay */}
            <div className={`${styles.mobileMenuOverlay} ${isMenuOpen ? styles.open : ''}`}>
                <div className={styles.mobileMenuHeader}>
                    <span className={styles.mobileMenuTitle}>메뉴</span>
                    <button className={styles.closeBtn} onClick={closeMenu}>
                        <X size={24} color="#3e2723" />
                    </button>
                </div>
                <nav className={styles.mobileNav}>
                    <Link href="/ocr" className={styles.mobileNavLink} onClick={closeMenu}>
                        📸 이미지로 전통주 찾기
                    </Link>
                    <Link href="/?view=list#body-section" className={styles.mobileNavLink} onClick={closeMenu}>
                        🍶 전통주 리스트
                    </Link>
                    <Link href="/map" className={styles.mobileNavLink} onClick={closeMenu}>
                        🗺️ 주막 지도
                    </Link>
                    <Link href="/board" className={styles.mobileNavLink} onClick={closeMenu}>
                        💬 커뮤니티
                    </Link>
                    <Link href="/mypage" className={styles.mobileNavLink} onClick={closeMenu}>
                        👤 마이페이지
                    </Link>
                </nav>
            </div>
        </header >
    );
}
