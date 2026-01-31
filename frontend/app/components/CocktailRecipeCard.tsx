"use client";

import React from 'react';
import styles from './CocktailRecipeCard.module.css';

interface CocktailRecipe {
    name: string;
    ingredients: string[];
    instructions: string[];
    base_liquor?: string;
    alcohol_content?: string;
}

interface CocktailRecipeCardProps {
    data: CocktailRecipe;
}

const CocktailRecipeCard: React.FC<CocktailRecipeCardProps> = ({ data }) => {
    return (
        <div className={styles.cardContainer}>
            <div className={styles.header}>
                <div className={styles.iconWrapper}>
                    🍸
                </div>
                <div className={styles.titleWrapper}>
                    <h3 className={styles.title}>{data.name}</h3>
                    {data.base_liquor && <span className={styles.subtitle}>Base: {data.base_liquor}</span>}
                </div>
            </div>

            <div className={styles.content}>
                <div className={styles.section}>
                    <h4 className={styles.sectionTitle}>재료 (Ingredients)</h4>
                    <ul className={styles.ingredientList}>
                        {data.ingredients.map((ing, idx) => (
                            <li key={idx} className={styles.ingredientItem}>{ing}</li>
                        ))}
                    </ul>
                </div>

                <div className={styles.divider}></div>

                <div className={styles.section}>
                    <h4 className={styles.sectionTitle}>제조법 (Instructions)</h4>
                    <ol className={styles.instructionList}>
                        {data.instructions.map((inst, idx) => (
                            <li key={idx} className={styles.instructionItem}>
                                <span className={styles.stepNum}>{idx + 1}.</span>
                                <span>{inst}</span>
                            </li>
                        ))}
                    </ol>
                </div>
            </div>
        </div>
    );
};

export default CocktailRecipeCard;
