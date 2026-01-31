"use client";

import { useEffect, useState } from "react";
import styles from "./SideDock.module.css";

const SECTIONS = [
    { id: "hero-section", label: "홈", icon: "Home", activeColor: "#fff" },
    { id: "body-section", label: "리스트 / 지도", icon: "List", activeColor: "#fff" },
    { id: "info-section", label: "추천 / 수상작", icon: "Info", activeColor: "#fff" },
];

export default function SideDock() {
    const [activeSection, setActiveSection] = useState("hero-section");

    // Scroll to section handler
    const handleScrollTo = (id: string) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: "smooth" });
        }
    };

    // Track active section on scroll
    useEffect(() => {
        const observerOptions = {
            root: null,
            rootMargin: "0px",
            threshold: 0.5, // 50% visibility required to be "active"
        };

        const observerCallback = (entries: IntersectionObserverEntry[]) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    setActiveSection(entry.target.id);
                }
            });
        };

        const observer = new IntersectionObserver(observerCallback, observerOptions);

        SECTIONS.forEach(({ id }) => {
            const element = document.getElementById(id);
            if (element) observer.observe(element);
        });

        return () => observer.disconnect();
    }, []);

    return (
        <div className={styles.dockContainer}>
            {SECTIONS.map((section) => (
                <div
                    key={section.id}
                    className={`${styles.dockItem} ${activeSection === section.id ? styles.active : ""}`}
                    onClick={() => handleScrollTo(section.id)}
                    data-label={section.label}
                >
                    {renderIcon(section.icon)}
                </div>
            ))}
        </div>
    );
}

function renderIcon(name: string) {
    if (name === "Home") {
        return (
            <svg xmlns="http://www.w3.org/2000/svg" className={styles.icon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
        );
    }
    if (name === "List") {
        return (
            <svg xmlns="http://www.w3.org/2000/svg" className={styles.icon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
        );
    }
    if (name === "Info") {
        return (
            <svg xmlns="http://www.w3.org/2000/svg" className={styles.icon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        );
    }
    return null;
}
