"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { useSession, signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import styles from "./board.module.css";
import { api } from '@/lib/api';

interface FlavorProfile {
    sweet: number;
    sour: number;
    body: number;
    scent: number;
    throat: number;
}

// Update Interface
interface TastingNote {
    _id: string;
    liquor_id: number;
    liquor_name: string;
    rating: number;
    flavor_profile: FlavorProfile;
    content: string;
    tags: string[];
    images: string[];
    created_at: string;
    user_id: string;
    author_name?: string;
    // 🆕 New fields
    drinking_temperature?: 'cold' | 'room' | 'warm';
    pairing_foods?: string[];
    atmosphere?: string;
    seasons?: string[];
    purchase_location?: string;
    liked_by?: string[]; // 🆕 Added field
}

export default function BoardPage() {
    const [posts, setPosts] = useState<TastingNote[]>([]);
    const [filteredPosts, setFilteredPosts] = useState<TastingNote[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [currentLimit, setCurrentLimit] = useState(20);

    // 🆕 Modal State
    const [selectedPost, setSelectedPost] = useState<TastingNote | null>(null);

    // 🆕 Filter state
    const [filters, setFilters] = useState({
        season: [] as string[],
        temperature: '' as string,
        atmosphere: '' as string,
        searchFood: '' as string
    });

    // 🆕 Login Modal State
    const [showLoginModal, setShowLoginModal] = useState(false);
    const router = useRouter();
    const { data: session } = useSession();

    useEffect(() => {
        fetchPosts();
    }, []);

    // 🆕 Apply filters when posts or filters change
    useEffect(() => {
        applyFilters();
    }, [posts, filters]);

    const fetchPosts = async (limit = 20) => {
        try {
            const data = await api.notes.getAll(limit);
            setPosts(data);
            setHasMore(data.length >= limit); // If we got full limit, there might be more
        } catch (error) {
            console.error("Error fetching posts:", error);
        } finally {
            setLoading(false);
        }
    };

    const loadMorePosts = async () => {
        if (loadingMore || !hasMore) return;
        setLoadingMore(true);
        try {
            const newLimit = currentLimit + 20;
            const data = await api.notes.getAll(newLimit);
            setPosts(data);
            setCurrentLimit(newLimit);
            setHasMore(data.length >= newLimit);
        } catch (error) {
            console.error("Error loading more posts:", error);
        } finally {
            setLoadingMore(false);
        }
    };

    // 🆕 Like Handler
    const handleLike = async (e: React.MouseEvent, post: TastingNote) => {
        e.stopPropagation(); // Prevent modal opening

        // if (!session?.user) {
        //     setShowLoginModal(true);
        //     return;
        // }

        const userId = (session?.user as any)?.id || session?.user?.email || "anonymous_user";
        if (!userId) return;

        // Optimistic Update
        const isLiked = post.liked_by?.includes(userId);
        const newLikeds = isLiked
            ? post.liked_by?.filter(id => id !== userId)
            : [...(post.liked_by || []), userId];

        const updatedPost = { ...post, liked_by: newLikeds };

        // Update local state immediately
        setPosts(prev => prev.map(p => p._id === post._id ? updatedPost : p));
        if (selectedPost && selectedPost._id === post._id) {
            setSelectedPost(updatedPost);
        }

        try {
            await api.notes.toggleLike(post._id, userId);
        } catch (err) {
            console.error(err);
            fetchPosts(); // Revert on failure
        }
    };

    // 🆕 Filter logic
    const applyFilters = () => {
        let filtered = [...posts];

        const hasActiveFilter =
            filters.season.length > 0 ||
            filters.temperature !== '' ||
            filters.atmosphere !== '' ||
            filters.searchFood !== '';

        if (!hasActiveFilter) {
            setFilteredPosts(posts);
            return;
        }

        if (filters.season.length > 0) {
            filtered = filtered.filter(post =>
                post.seasons?.some(s => filters.season.includes(s))
            );
        }
        if (filters.temperature) {
            filtered = filtered.filter(post =>
                post.drinking_temperature === filters.temperature
            );
        }
        if (filters.atmosphere) {
            filtered = filtered.filter(post =>
                post.atmosphere === filters.atmosphere
            );
        }
        if (filters.searchFood) {
            filtered = filtered.filter(post =>
                post.pairing_foods?.some(food =>
                    food.toLowerCase().includes(filters.searchFood.toLowerCase())
                )
            );
        }

        setFilteredPosts(filtered);
    };

    const resetFilters = () => {
        setFilters({ season: [], temperature: '', atmosphere: '', searchFood: '' });
    };

    // Prevent body scroll when modal is open
    useEffect(() => {
        if (selectedPost) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
    }, [selectedPost]);

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.contentWrapper} style={{ textAlign: "center", paddingTop: "200px" }}>
                    Loading Community... 🍶
                </div>
            </div>
        );
    }

    // Helper to check like status
    const isLikedByMe = (post: TastingNote) => {
        // if (!session?.user) return false;
        const userId = (session?.user as any)?.id || session?.user?.email || "anonymous_user";
        return post.liked_by?.includes(userId);
    };

    return (
        <div className={styles.container}>
            <div className={styles.background}>
                <Image src="/jumak.png" alt="Background" fill style={{ objectFit: "cover" }} priority />
                <div className={styles.overlay} />
            </div>

            <div className={styles.header}>
                <h1 className={styles.title}>🍶 우리들의 주막</h1>
                <button
                    className={styles.writeButton}
                    onClick={() => {
                        // if (!session) setShowLoginModal(true);
                        // else router.push('/board/write');
                        router.push('/board/write');
                    }}
                >
                    <span>✍️</span> 시음 노트 쓰기
                </button>
            </div>

            {/* Login Required Modal */}
            {showLoginModal && (
                <div className={styles.modalOverlay} onClick={() => setShowLoginModal(false)}>
                    <div className={styles.authCard} onClick={e => e.stopPropagation()}>
                        <button className={styles.closeButton} onClick={() => setShowLoginModal(false)}>✕</button>
                        <h2>로그인이 필요합니다</h2>
                        <p>좋아요를 누르거나 글을 쓰려면 로그인이 필요합니다.</p>
                        <button className={styles.authButton} onClick={() => signIn("cognito", { callbackUrl: "/board/write" })}>
                            로그인하기
                        </button>
                    </div>
                </div>
            )}

            {/* Filter Section (Hidden/Collapsed by default or simplified) */}
            {/* For now, keeping it simpler or just the content */}

            <div className={styles.grid}>
                {filteredPosts.map((post) => (
                    <div
                        key={post._id}
                        className={styles.card}
                        onClick={() => setSelectedPost(post)}
                    >
                        {/* 1:1 Square Image Area */}
                        <div className={styles.imageArea}>
                            {post.images && post.images.length > 0 ? (
                                <img src={post.images[0]} alt={post.liquor_name} className={styles.cardImage} />
                            ) : (
                                <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ccc', fontSize: '2rem' }}>
                                    🍶
                                </div>
                            )}
                            {/* Hover Overlay */}
                            <div className={styles.cardOverlay} />
                        </div>

                        {/* Content Below */}
                        <div className={styles.cardContent}>
                            <h3 className={styles.cardTitle}>{post.liquor_name}</h3>
                            <p className={styles.cardPreview}>{post.content}</p>

                            <div className={styles.cardMeta}>
                                <span className={styles.rating}>⭐ {post.rating}</span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <span>{post.author_name || "익명"}</span>
                                    {/* Like Button on Card */}
                                    <button
                                        onClick={(e) => handleLike(e, post)}
                                        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem' }}
                                    >
                                        {isLikedByMe(post) ? '❤️' : '🤍'} {post.liked_by?.length || 0}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Detail Modal */}
            {selectedPost && (
                <div className={styles.modalOverlay} onClick={() => setSelectedPost(null)}>
                    <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
                        {/* Left: Image */}
                        <div className={styles.modalImageSection}>
                            {selectedPost.images && selectedPost.images.length > 0 ? (
                                <img src={selectedPost.images[0]} alt={selectedPost.liquor_name} className={styles.fullImage} />
                            ) : (
                                <div style={{ color: 'white' }}>이미지가 없습니다</div>
                            )}
                        </div>

                        {/* Right: Info */}
                        <div className={styles.modalInfoSection}>
                            <button className={styles.closeButton} onClick={() => setSelectedPost(null)}>✕</button>

                            <h2 className={styles.modalTitle}>{selectedPost.liquor_name}</h2>
                            <div className={styles.modalMeta}>
                                <span className={styles.ratingBadge}>⭐ {selectedPost.rating}점</span>
                                <span>👤 {selectedPost.author_name || "익명"}</span>

                                <button
                                    onClick={(e) => handleLike(e, selectedPost)}
                                    style={{
                                        background: 'none',
                                        border: '1px solid #eee',
                                        borderRadius: '20px',
                                        padding: '5px 15px',
                                        cursor: 'pointer',
                                        fontSize: '1rem',
                                        marginLeft: 'auto',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '5px'
                                    }}
                                >
                                    {isLikedByMe(selectedPost) ? '❤️' : '🤍'} 좋아요 {selectedPost.liked_by?.length || 0}
                                </button>
                            </div>

                            <div className={styles.modalBody}>
                                {selectedPost.content}
                            </div>

                            <div className={styles.tagGroup}>
                                {selectedPost.tags.map((tag, idx) => (
                                    <span key={idx} className={styles.tag}>#{tag}</span>
                                ))}
                            </div>

                            {/* Flavor Chart */}
                            <div className={styles.modalChart}>
                                <h4 style={{ marginBottom: '15px', color: '#555' }}>맛 그래프</h4>
                                <div style={{ width: '100%', height: 250 }}>
                                    <ResponsiveContainer>
                                        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={[
                                            { subject: '🍯 단맛', A: selectedPost.flavor_profile.sweet, fullMark: 5 },
                                            { subject: '🍋 신맛', A: selectedPost.flavor_profile.sour, fullMark: 5 },
                                            { subject: '💧 목넘김', A: selectedPost.flavor_profile.throat, fullMark: 5 },
                                            { subject: '🏋️ 바디감', A: selectedPost.flavor_profile.body, fullMark: 5 },
                                            { subject: '⚖️ 균형감', A: Math.round((selectedPost.flavor_profile.sweet + selectedPost.flavor_profile.sour + selectedPost.flavor_profile.body + selectedPost.flavor_profile.scent + selectedPost.flavor_profile.throat) / 5), fullMark: 5 },
                                            { subject: '🌸 향', A: selectedPost.flavor_profile.scent, fullMark: 5 },
                                        ]}>
                                            <PolarGrid stroke="#8d6e63" strokeOpacity={0.3} />
                                            <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: '#4e342e', fontWeight: 600 }} />
                                            <PolarRadiusAxis angle={90} domain={[0, 5]} tick={false} axisLine={false} />
                                            <Radar name="맛" dataKey="A" stroke="#8d6e63" fill="#a1887f" fillOpacity={0.7} strokeWidth={2} />
                                        </RadarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            <div className={styles.modalActions}>
                                {session?.user?.email && ["admin@jumak.com", "dyddl1213@naver.com", "dyddl1213@gmail.com"].includes(session.user.email) && (
                                    <button
                                        onClick={async () => {
                                            if (confirm("관리자 권한으로 이 게시글을 삭제하시겠습니까? (복구 불가)")) {
                                                try {
                                                    await api.notes.delete(selectedPost._id);
                                                    alert("관리자 권한으로 삭제되었습니다.");
                                                    setSelectedPost(null);
                                                    fetchPosts();
                                                } catch (e) {
                                                    console.error(e);
                                                    alert("오류 발생");
                                                }
                                            }
                                        }}
                                        style={{
                                            marginRight: 'auto',
                                            background: '#ff5252',
                                            color: 'white',
                                            border: 'none',
                                            padding: '10px 20px',
                                            borderRadius: '8px',
                                            cursor: 'pointer',
                                            fontWeight: 'bold'
                                        }}
                                    >
                                        🗑️ 관리자 삭제
                                    </button>
                                )}
                                <Link href={`/drink/${selectedPost.liquor_id}`} className={styles.viewProductBtn}>
                                    🍶 이 술 자세히 보러가기
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
