"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import styles from "../board.module.css";

interface Post {
    id: string;
    title: string;
    content: string;
    author: string;
    created_at: string;
}

export default function PostDetailPage() {
    const params = useParams();
    const router = useRouter();
    const [post, setPost] = useState<Post | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (params.id) {
            fetchPost(params.id as string);
        }
    }, [params.id]);

    const fetchPost = async (id: string) => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            const response = await fetch(`${apiUrl}/board/${id}`);
            if (response.ok) {
                const data = await response.json();
                setPost(data);
            } else {
                console.error("Failed to fetch post");
            }
        } catch (error) {
            console.error("Error fetching post:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm("정말 삭제하시겠습니까?")) return;

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            const response = await fetch(`${apiUrl}/board/${params.id}`, {
                method: "DELETE",
            });

            if (response.ok) {
                router.push("/board");
                router.refresh();
            } else {
                alert("Failed to delete post");
            }
        } catch (error) {
            console.error("Error deleting post:", error);
            alert("An error occurred");
        }
    };

    if (loading) return <div className={styles.container}>Loading...</div>;
    if (!post) return <div className={styles.container}>Post not found</div>;

    return (
        <div className={styles.container}>
            <div className={styles.background}>
                <Image
                    src="/jumak.png"
                    alt="Background"
                    fill
                    style={{ objectFit: "cover" }}
                    priority
                />
                <div className={styles.overlay} />
            </div>

            <div className={styles.detailContainer}>
                <Link href="/board" className={styles.backButton}>
                    ← 목록으로 돌아가기
                </Link>

                <h1 className={styles.detailTitle}>{post.title}</h1>

                <div className={styles.detailMeta}>
                    <span>작성자: {post.author}</span>
                    <span>{new Date(post.created_at).toLocaleString()}</span>
                </div>

                <div className={styles.detailContent}>
                    {post.content}
                </div>

                <div style={{ marginTop: "2rem", borderTop: "1px solid #eee", paddingTop: "1rem" }}>
                    <button
                        onClick={handleDelete}
                        style={{
                            background: "#ff4444",
                            color: "white",
                            border: "none",
                            padding: "0.5rem 1rem",
                            borderRadius: "4px",
                            cursor: "pointer"
                        }}
                    >
                        삭제하기
                    </button>
                </div>
            </div>
        </div>
    );
}
