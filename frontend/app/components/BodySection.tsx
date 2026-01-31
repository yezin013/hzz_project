"use client";

import { useState, useRef, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import styles from "./BodySection.module.css";
import ProductGridSection from "./ProductGridSection";
import MapSection from "./MapSection";

interface BodySectionProps {
    searchQuery: string;
}

export default function BodySection({ searchQuery }: BodySectionProps) {
    const searchParams = useSearchParams();
    const [activeTab, setActiveTab] = useState<'grid' | 'map'>('grid');

    // Ref for scrolling to this section
    const sectionRef = useRef<HTMLElement>(null);

    // If search query changes (and is not empty), auto switch to grid view
    useEffect(() => {
        if (searchQuery) {
            setActiveTab('grid');
        } else {
            // Check for view param
            const viewParam = searchParams.get('view');
            if (viewParam === 'map') {
                setActiveTab('map');
            } else if (viewParam === 'list') {
                setActiveTab('grid');
            }
        }
    }, [searchQuery, searchParams]);

    return (
        <section ref={sectionRef} id="body-section" className={styles.bodySection}>


            {/* Content Area */}
            <div className={styles.contentArea}>
                <ProductGridSection initialQuery={searchQuery} />
            </div>
        </section>
    );
}
