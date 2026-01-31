"use client";

import { useSession, signIn } from "next-auth/react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import styles from "./page.module.css";
import Link from "next/link";
import { api } from '@/lib/api';

interface FlavorProfile {
    sweet: number;
    sour: number;
    body: number;
    scent: number;
    throat: number;
}

interface TastingNote {
    _id: string;
    liquor_id: number;
    liquor_name: string;
    rating: number;
    flavor_profile: FlavorProfile;
    content: string;
    tags: string[];
    created_at: string;
}

interface Favorite {
    id: string;
    user_id: string;
    drink_id: number;
    drink_name: string;
    image_url?: string;
    created_at: string;
}

export default function MyPage() {
    const { data: session, status } = useSession();
    const router = useRouter();
    const [notes, setNotes] = useState<TastingNote[]>([]);
    const [favorites, setFavorites] = useState<Favorite[]>([]);
    const [loading, setLoading] = useState(true);
    const [favoritesLoading, setFavoritesLoading] = useState(false);
    const [activeTab, setActiveTab] = useState<'my_notes' | 'saved'>('my_notes');

    const fetchNotes = async (userId: string) => {
        try {
            setLoading(true);
            const data = await api.notes.getByUserId(userId);
            setNotes(data);
        } catch (error) {
            console.error("Error fetching notes:", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchFavorites = async (userId: string) => {
        try {
            setFavoritesLoading(true);
            const data = await api.favorites.getByUserId(userId);
            setFavorites(data);
        } catch (error) {
            console.error("Error fetching favorites:", error);
        } finally {
            setFavoritesLoading(false);
        }
    };

    const handleRemoveFavorite = async (drinkId: number) => {
        if (!session?.user) return;
        if (!confirm("정말 찜을 해제하시겠습니까?")) return;

        try {
            const user = session.user as any;
            const userId = user.id || user.email;
            await api.favorites.remove(userId, drinkId);

            // Refresh list
            fetchFavorites(userId);
            alert("찜이 해제되었습니다.");
        } catch (error) {
            console.error("Error removing favorite:", error);
            alert("오류가 발생했습니다.");
        }
    };

    // Auto-redirect removed for better UI
    /*
    useEffect(() => {
        if (status === 'unauthenticated') {
            signIn("cognito", { callbackUrl: "/mypage" });
        }
    }, [status]);
    */

    useEffect(() => {
        if (session?.user) {
            const user = session.user as any;
            const userId = user.id || user.email;
            if (userId) {
                fetchNotes(userId);
                fetchFavorites(userId);
            }
        }
    }, [session]);

    if (status === "loading" || loading) {
        return (
            <div className={styles.container} style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
                <div style={{ textAlign: 'center', color: '#8d6e63' }}>
                    <p style={{ fontSize: '1.2rem', fontWeight: '600' }}>로그인 확인 중...</p>
                </div>
            </div>
        );
    }

    // Only render dashboard if session exists
    // Only render dashboard if session exists
    if (!session) {
        return (
            <div className={styles.container}>
                <div className={styles.authOverlay}>
                    <div className={styles.authCard}>
                        <div className={styles.authIcon}>🔒</div>
                        <h2 className={styles.authTitle}>로그인이 필요합니다</h2>
                        <p className={styles.authDescription}>
                            나만의 전통주 창고를 관리하려면<br />로그인이 필요합니다
                        </p>
                        <button
                            className={styles.authButton}
                            onClick={() => signIn("cognito", { callbackUrl: "/mypage" })}
                        >
                            로그인하기
                        </button>
                    </div>
                </div>
                {/* Background blurred content preview could go here if desired, 
                    but for page security we just show the card */}
            </div>
        );
    }

    return (
        <div className={styles.container}>
            {/* 🆕 Profile Dashboard Header */}
            <div className={styles.profileHeader}>
                <div className={styles.profileDecoration} />
                <div className={styles.avatar}>
                    {session.user?.name?.[0] || "U"}
                </div>
                <div className={styles.profileInfo}>
                    <h1 className={styles.profileName}>{session.user?.name}님의 양조장</h1>
                    <p className={styles.profileEmail}>{session.user?.email}</p>

                    <div className={styles.statsRow}>
                        <div className={styles.statItem}>
                            <span className={styles.statValue}>{notes.length}</span>
                            <span className={styles.statLabel}>시음 노트</span>
                        </div>
                        <div className={styles.statItem}>
                            <span className={styles.statValue}>0</span>
                            <span className={styles.statLabel}>찜한 전통주</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* 🆕 Tab Navigation */}
            <div className={styles.tabsContainer}>
                <button
                    className={`${styles.tabButton} ${activeTab === 'my_notes' ? styles.active : ''}`}
                    onClick={() => setActiveTab('my_notes')}
                >
                    📝 시음 노트
                </button>
                <button
                    className={`${styles.tabButton} ${activeTab === 'saved' ? styles.active : ''}`}
                    onClick={() => setActiveTab('saved')}
                >
                    💖 찜한 술
                </button>
            </div>

            {/* Tab Content */}
            {activeTab === 'my_notes' && (
                <div>
                    <div className={styles.sectionTitle}>
                        {notes.length === 0 ? <h2>아직 작성한 노트가 없어요</h2> : <h2>총 {notes.length}개의 기록</h2>}
                        <Link href="/board/write" className={styles.writeButtonLink}>
                            + 새 노트 작성
                        </Link>
                    </div>

                    {notes.length === 0 ? (
                        <div className={styles.emptyState}>
                            <p>전통주를 마시고 나만의 기록을 남겨보세요! 🍶</p>
                        </div>
                    ) : (
                        <div className={styles.notesGrid}>
                            {notes.map((note) => (
                                <div key={note._id} className={styles.noteCard}>
                                    <h3 className={styles.liquorName}>{note.liquor_name}</h3>

                                    <div className={styles.chartContainer}>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={[
                                                { subject: '🍯 단맛', A: note.flavor_profile.sweet, fullMark: 5 },
                                                { subject: '🍋 신맛', A: note.flavor_profile.sour, fullMark: 5 },
                                                { subject: '💧 목넘김', A: note.flavor_profile.throat, fullMark: 5 },
                                                { subject: '🏋️ 바디감', A: note.flavor_profile.body, fullMark: 5 },
                                                { subject: '⚖️ 균형감', A: Math.round((note.flavor_profile.sweet + note.flavor_profile.sour + note.flavor_profile.body + note.flavor_profile.scent + note.flavor_profile.throat) / 5), fullMark: 5 },
                                                { subject: '🌸 향', A: note.flavor_profile.scent, fullMark: 5 },
                                            ]}>
                                                <PolarGrid stroke="#8d6e63" strokeOpacity={0.3} />
                                                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#4e342e', fontWeight: 600 }} />
                                                <PolarRadiusAxis angle={90} domain={[0, 5]} tick={false} axisLine={false} />
                                                <Radar name="맛" dataKey="A" stroke="#8d6e63" fill="#a1887f" fillOpacity={0.7} strokeWidth={2} />
                                            </RadarChart>
                                        </ResponsiveContainer>
                                    </div>

                                    <div className={styles.noteContent}>{note.content}</div>

                                    <div className={styles.tags}>
                                        <span className={styles.tag}>⭐ {note.rating}</span>
                                        {note.tags.map(tag => <span key={tag} className={styles.tag}>{tag}</span>)}
                                    </div>

                                    <div className={styles.actions}>
                                        <button
                                            onClick={() => router.push(`/board/write?edit=${note._id}`)}
                                            className={styles.editButton}
                                        >
                                            수정
                                        </button>
                                        <button
                                            onClick={async () => {
                                                if (confirm("정말 삭제하시겠습니까?")) {
                                                    try {
                                                        await api.notes.delete(note._id);
                                                        alert("삭제되었습니다.");
                                                        fetchNotes((session?.user as any).id || session?.user?.email);
                                                    } catch (err) {
                                                        console.error(err);
                                                        alert("삭제에 실패했습니다.");
                                                    }
                                                }
                                            }}
                                            className={styles.deleteButton}
                                        >
                                            삭제
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )
            }

            {
                activeTab === 'saved' && (
                    <div>
                        <div className={styles.sectionTitle}>
                            {favorites.length === 0 ? <h2>찜한 술이 없어요</h2> : <h2>총 {favorites.length}개의 찜</h2>}
                        </div>

                        {favoritesLoading ? (
                            <div className={styles.emptyState}>
                                <p>찜 목록을 불러오는 중... 🍶</p>
                            </div>
                        ) : favorites.length === 0 ? (
                            <div className={styles.emptyState}>
                                <p>술 상세 페이지에서 ❤️를 눌러 찜해보세요!</p>
                                <Link href="/" className={styles.writeButtonLink} style={{ marginTop: '20px', display: 'inline-block' }}>
                                    술 찾으러 가기
                                </Link>
                            </div>
                        ) : (
                            <div className={styles.notesGrid}>
                                {favorites.map((fav) => (
                                    <div key={fav.id} className={styles.noteCard} style={{ cursor: 'pointer', position: 'relative' }}>
                                        {/* Remove button */}
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleRemoveFavorite(fav.drink_id);
                                            }}
                                            style={{
                                                position: 'absolute',
                                                top: '10px',
                                                right: '10px',
                                                background: 'rgba(255,255,255,0.9)',
                                                border: 'none',
                                                borderRadius: '50%',
                                                width: '32px',
                                                height: '32px',
                                                cursor: 'pointer',
                                                fontSize: '1.2rem',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                                                zIndex: 10
                                            }}
                                            title="찜 해제"
                                        >
                                            ❤️
                                        </button>

                                        {/* Click to go to drink detail */}
                                        <div onClick={() => router.push(`/drink/${fav.drink_id}`)}>
                                            {fav.image_url ? (
                                                <div style={{
                                                    width: '100%',
                                                    height: '180px',
                                                    background: '#f8f9fa',
                                                    borderRadius: '12px',
                                                    overflow: 'hidden',
                                                    marginBottom: '15px'
                                                }}>
                                                    <img
                                                        src={`/api/image-proxy?url=${encodeURIComponent(fav.image_url)}`}
                                                        alt={fav.drink_name}
                                                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                                    />
                                                </div>
                                            ) : (
                                                <div style={{
                                                    width: '100%',
                                                    height: '180px',
                                                    background: 'linear-gradient(135deg, #f5f5f5, #e0e0e0)',
                                                    borderRadius: '12px',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    fontSize: '3rem',
                                                    marginBottom: '15px'
                                                }}>
                                                    🍶
                                                </div>
                                            )}
                                            <h3 className={styles.liquorName}>{fav.drink_name}</h3>
                                            <p style={{ fontSize: '0.85rem', color: '#888', marginTop: '8px' }}>
                                                {new Date(fav.created_at).toLocaleDateString('ko-KR')}에 찜함
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )
            }
        </div >
    );
}
